import logging
import os

import typer

from .aws.asg import AWSAutoscalingGroup

logger = logging.getLogger("asgd")
logger.setLevel(logging.getLevelName(os.getenv("ASGD_LOG_LEVEL", "INFO")))
logger.addHandler(logging.StreamHandler())

app = typer.Typer(name="asgd")


@app.callback()
def callback():
    """
    AWS ASG Deployer
    """


@app.command()
def deploy(
    asg_name: str,
    ami: str = typer.Option(None),
    step_size: int = typer.Option(1),
    auto_approve: bool = typer.Option(False, "--auto-approve"),
    deployment_timeout_seconds: int = typer.Option(900),
    instance_timeout_seconds: int = typer.Option(180),
):
    """
    Updates Autoscaling Group to use new AMI if provided and then performs an instance
    refresh.
    """

    asg = AWSAutoscalingGroup(
        name=asg_name,
        deployment_timeout_seconds=deployment_timeout_seconds,
        instance_timeout_seconds=instance_timeout_seconds,
    )

    if ami:
        launch_template = asg.launch_template
        typer.echo(
            f"Creating new default launch template version for {launch_template.id}"
        )
        new_version = launch_template.create_new_default_version(
            launch_template_data={"ImageId": ami}
        )
        typer.echo(f"Launch Template version {new_version} successfully created")
        if not auto_approve:
            typer.confirm(
                f"Do you want to apply this new version to the {asg_name} ASG (this will not refresh instances yet)?",
                abort=True,
            )
        typer.echo(
            f"Updating ASG to use launch template {launch_template.id} version {new_version}"
        )
        asg.set_launch_template_version(version=new_version)

    if not auto_approve:
        typer.confirm(f"Refresh instances in {asg_name} ASG?", abort=True)
    typer.echo(f"Refreshing instances in Autoscaling group {asg_name}")
    asg.refresh_instances(step_size)
