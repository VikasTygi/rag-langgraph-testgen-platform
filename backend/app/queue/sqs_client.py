import json
from typing import Any

import boto3

from app.config import settings


sqs = boto3.client(
    "sqs",
    region_name=settings.aws_region,
)


def send_generation_job(job: dict[str, Any]):
    return sqs.send_message(
        QueueUrl=settings.sqs_generation_queue_url,
        MessageBody=json.dumps(job),
        MessageAttributes={
            "generation_id": {
                "DataType": "String",
                "StringValue": job["generation_id"],
            },
            "user_id": {
                "DataType": "String",
                "StringValue": job["user_id"],
            },
        },
    )


def receive_generation_jobs(max_messages: int = 5):
    return sqs.receive_message(
        QueueUrl=settings.sqs_generation_queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=20,
        VisibilityTimeout=300,
        MessageAttributeNames=["All"],
    ).get("Messages", [])


def delete_generation_job(receipt_handle: str):
    return sqs.delete_message(
        QueueUrl=settings.sqs_generation_queue_url,
        ReceiptHandle=receipt_handle,
    )