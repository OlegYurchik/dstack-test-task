import contextlib
import datetime
import logging
import threading
from queue import Empty, Queue

import docker


logger = logging.getLogger(__name__)
MAX_LOG_EVENTS_COUNT = 10_000


@contextlib.contextmanager
def _read_logs_exit(container, end_event: threading.Event):
    try:
        yield
    finally:
        container.remove(force=True)
        end_event.set()


def read_logs(queue: Queue, end_event: threading.Event, image: str, command: str | list[str]):
    container = docker.from_env().containers.run(
        image=image,
        command=command,
        detach=True,
        auto_remove=True,
        environment={"PYTHONUNBUFFERED": "1"},
    )
    with _read_logs_exit(container=container, end_event=end_event):
        for log in container.logs(stream=True, timestamps=True):
            timestamp_raw, message_raw = log.split(b" ", maxsplit=1)
            timestamp = datetime.datetime.fromisoformat(timestamp_raw.decode("utf-8"))
            timestamp = int(timestamp.timestamp() * 1000)
            message = message_raw.decode("utf-8")

            queue.put({"timestamp": timestamp, "message": message})


def _send_logs(queue: Queue, client, group: str, stream: str):
    log_events = []
    while len(log_events) < MAX_LOG_EVENTS_COUNT:
        try:
            log_event = queue.get_nowait()
        except Empty:
            break
        else:
            log_events.append(log_event)
    if log_events:
        client.put_log_events(logGroupName=group, logStreamName=stream, logEvents=log_events)
        logger.info("Send %d event logs", len(log_events))


def send_logs(queue: Queue, end_event: threading.Event, client, group: str, stream: str):
    while not end_event.is_set():
        _send_logs(queue=queue, client=client, group=group, stream=stream)
    _send_logs(queue=queue, client=client, group=group, stream=stream)
