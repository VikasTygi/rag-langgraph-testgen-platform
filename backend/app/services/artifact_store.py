import os
from datetime import datetime, timezone

import boto3


class S3ArtifactStore:
    def __init__(self):
        self.bucket = os.getenv("ARTIFACT_BUCKET")
        if not self.bucket:
            raise RuntimeError("ARTIFACT_BUCKET environment variable is not configured")

        self.client = boto3.client("s3")

    def save_generated_code(
        self,
        generation_id: str,
        framework: str,
        code: str,
    ) -> str:
        now = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        extension = {
            "robot": "robot",
            "pytest": "py",
            "playwright": "ts",
        }.get(framework, "txt")

        key = f"generations/{now}/{generation_id}/generated.{extension}"

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=code.encode("utf-8"),
            ContentType="text/plain",
        )

        return key

    def presign_get_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
            },
            ExpiresIn=expires_in,
        )