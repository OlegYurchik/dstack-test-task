# Test Task dstack.ai

[Description](./Backend Engineer Test Task.pdf)

## Installation

```shell
git clone https://github.com/OlegYurchik/dstack-test-task
cd dstack-test-task
pip install poetry
poetry install
```

## Run

```shell
python -m dstack_test_task \
    --docker-image python \
    --bash-command $'pip install pip -U && pip install tqdm && python -c \"import time\ncounter = 0\nwhile True:\n\tprint(counter)\n\tcounter = counter + 1\n\ttime.sleep(0.1)\"' \
    --aws-cloudwatch-group test-task-group-1 \
    --aws-cloudwatch-stream test-task-stream-1 \
    --aws-access-key-id ... \
    --aws-secret-access-key ... \
    --aws-region ...
```

## TODO

1. Fix bug when event log batch more then `1,048,576` bytes. Check corner cases from
[`put_log_events` documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/put_log_events.html#CloudWatchLogs.Client.put_log_events)
