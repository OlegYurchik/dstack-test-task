import contextlib
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import boto3
import typer
from botocore.config import Config

from . import tasks
from .logging import catch


logger = logging.getLogger(__name__)
QUEUE_MAX_SIZE = 10000


@catch(logger)
def entrypoint(
        docker_image: str = typer.Option(..., "--docker-image", help="Docker image name"),
        bash_command: str = typer.Option(..., "--bash-command", help="Container entry command"),
        aws_cloudwatch_group: str = typer.Option(
            ...,
            "--aws-cloudwatch-group",
            help="AWS CloudWatch Logs group name",
        ),
        aws_cloudwatch_stream: str = typer.Option(
            ...,
            "--aws-cloudwatch-stream",
            help="AWS CloudWatch Logs stream name",
        ),
        aws_access_key_id: str = typer.Option(..., "--aws-access-key-id", help="AWS access key ID"),
        aws_secret_access_key: str = typer.Option(
            ...,
            "--aws-secret-access-key",
            help="AWS secret access key",
        ),
        aws_region: str = typer.Option(..., "--aws-region", help="AWS region"),
):
    cloudwatch_logs_client = boto3.client(
        "logs",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        config=Config(region_name=aws_region, retries={"max_attempts": 10, "mode": "adaptive"}),
    )
    with contextlib.suppress(cloudwatch_logs_client.exceptions.ResourceAlreadyExistsException):
        cloudwatch_logs_client.create_log_group(logGroupName=aws_cloudwatch_group)
    with contextlib.suppress(cloudwatch_logs_client.exceptions.ResourceAlreadyExistsException):
        cloudwatch_logs_client.create_log_stream(
            logGroupName=aws_cloudwatch_group,
            logStreamName=aws_cloudwatch_stream,
        )

    queue = Queue(maxsize=QUEUE_MAX_SIZE)
    end_event = threading.Event()
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(
            tasks.read_logs,
            queue=queue,
            end_event=end_event,
            image=docker_image,
            command=bash_command,
        )
        executor.submit(
            tasks.send_logs,
            queue=queue,
            end_event=end_event,
            client=cloudwatch_logs_client,
            group=aws_cloudwatch_group,
            stream=aws_cloudwatch_stream,
        )


def get_cli() -> typer.Typer:
    cli = typer.Typer()

    cli.command()(entrypoint)

    return cli
