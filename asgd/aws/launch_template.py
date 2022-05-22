import logging

import boto3
from botocore.config import Config

logger = logging.getLogger("asgd")


class AWSLaunchTemplate:
    """
    AWS Launch Template.
    """

    client = boto3.client(
        "ec2", config=Config(retries={"max_attempts": 20, "mode": "standard"})
    )

    def __init__(self, id, current_version):
        self.id = id
        self.current_version = current_version
        self.description = None

        self.get_description()

    def get_description(self):
        describe_launch_templates = self.client.describe_launch_templates(
            LaunchTemplateIds=[self.id]
        )
        logger.debug(describe_launch_templates)
        description = describe_launch_templates["LaunchTemplates"][0]
        self.description = description

    def create_new_default_version(self, launch_template_data):
        create_launch_template_version = self.client.create_launch_template_version(
            LaunchTemplateId=self.id,
            SourceVersion=self.current_version,
            LaunchTemplateData=launch_template_data,
        )
        logger.debug(create_launch_template_version)
        version = str(
            create_launch_template_version["LaunchTemplateVersion"]["VersionNumber"]
        )
        modify_launch_template = self.client.modify_launch_template(
            LaunchTemplateId=self.id, DefaultVersion=version
        )
        logger.debug(modify_launch_template)
        return version
