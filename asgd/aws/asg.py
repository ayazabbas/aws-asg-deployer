import logging
import time
from datetime import datetime

import typer

import boto3
from botocore.config import Config

from .launch_template import AWSLaunchTemplate

logger = logging.getLogger("asgd")


class AWSAutoscalingGroup:
    """
    AWS Autoscaling Group
    """

    client = boto3.client(
        "autoscaling", config=Config(retries={"max_attempts": 20, "mode": "standard"})
    )

    def __init__(self, name, deployment_timeout_seconds, instance_timeout_seconds):
        self.name = name
        self.deployment_timeout_seconds = deployment_timeout_seconds
        self.instance_timeout_seconds = instance_timeout_seconds
        self.description = None
        self.launch_template = None

        self.get_description()
        self.get_launch_template()

        self.desired_capacity = self.description["DesiredCapacity"]

    def get_description(self):
        """
        Updates this Autoscaling Group's description instance attribute
        """
        describe_auto_scaling_groups = self.client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[self.name]
        )
        logger.debug(describe_auto_scaling_groups)
        description = describe_auto_scaling_groups["AutoScalingGroups"][0]
        self.description = description

    def get_launch_template(self):
        if not self.description:
            self.update_description
        launch_template_id = self.description["LaunchTemplate"]["LaunchTemplateId"]
        launch_template_version = self.description["LaunchTemplate"]["Version"]
        self.launch_template = AWSLaunchTemplate(
            id=launch_template_id, current_version=launch_template_version
        )

    def set_launch_template_version(self, version):
        update_auto_scaling_group = self.client.update_auto_scaling_group(
            AutoScalingGroupName=self.name,
            LaunchTemplate={
                "LaunchTemplateId": self.launch_template.id,
                "Version": str(version),
            },
        )
        logger.debug(update_auto_scaling_group)
        self.launch_template.current_version = version

    def is_capacity_met(self):
        """
        Checks if the number of healthy instances matches the desired capacity
        """
        self.get_description()

    def set_desired_capacity(self, desired_capacity):
        """
        Sets desired capacity and waits for it to be met
        """
        new_instance_start_time = datetime.now()
        response = self.client.set_desired_capacity(
            AutoScalingGroupName=self.name,
            DesiredCapacity=desired_capacity,
        )
        logger.debug(response)

        capacity_met = self.is_capacity_met()
        while not capacity_met:
            # Check if instance timeout is reached
            elapsed = (datetime.now() - new_instance_start_time).total_seconds()
            if elapsed >= self.instance_timeout_seconds:
                logger.error(
                    f"Timed out after {elapsed} seconds while waiting for desired capacity to be met"
                )
                exit(1)

            capacity_met = self.is_capacity_met()
            time.sleep(5)

    def refresh_instances(self, step_size: int):
        deployment_start_time = datetime.now()
        logger.debug("Getting updated ASG description")
        self.get_description()
        old_instance_ids = [i["InstanceId"] for i in self.description["Instances"]]

        refreshed = False
        while not refreshed:
            # Check if instance timeout is reached
            elapsed = (datetime.now() - deployment_start_time).total_seconds()
            if (elapsed) >= self.deployment_timeout_seconds:
                logger.error(f"Deployment timed out after {elapsed} seconds")
                exit(1)

            logger.debug("Getting updated ASG description")
            refreshed = True

            # Check if any old instances are still present in the ASG
            for i in self.description["Instances"]:
                if i["InstanceId"] in old_instance_ids:
                    refreshed = False

            if not refreshed:
                current_capacity = self.description["DesiredCapacity"]

                # Check if we need to add instances
                if current_capacity == self.desired_capacity:
                    # Increase desired capacity by step_size
                    typer.echo(f"Adding {step_size} new instances to ASG")
                    self.set_desired_capacity(
                        AutoScalingGroupName=self.name,
                        DesiredCapacity=current_capacity + step_size,
                    )

                # Check if we need to remove instances
                if current_capacity > self.desired_capacity:
                    # Decrease desired capacity by step_size
                    typer.echo(f"Removing {step_size} old instances from ASG")
                    self.client.set_desired_capacity(
                        AutoScalingGroupName=self.name,
                        DesiredCapacity=current_capacity - step_size,
                    )
