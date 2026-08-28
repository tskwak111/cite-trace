from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PutResult:
    key: str
    created: bool


class ObjectStore(Protocol):
    async def put_if_absent(self, key: str, data: bytes, media_type: str) -> PutResult: ...
    async def read(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> None: ...


def source_object_key(workspace_id: UUID, sha256_hex: str) -> str:
    return f"workspaces/{workspace_id}/source-assets/{sha256_hex[:2]}/{sha256_hex}.pdf"


class FakeObjectStore:
    """In-memory object store for testing — never use in production."""
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def put_if_absent(self, key: str, data: bytes, media_type: str) -> PutResult:
        if key in self._store:
            return PutResult(key=key, created=False)
        self._store[key] = data
        return PutResult(key=key, created=True)

    async def read(self, key: str) -> bytes:
        if key not in self._store:
            raise KeyError(key)
        return self._store[key]

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class S3ObjectStore:
    """S3-compatible immutable object store."""
    def __init__(self, endpoint_url: str, bucket: str, access_key: str, secret_key: str) -> None:
        import boto3
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._bucket = bucket

    async def put_if_absent(self, key: str, data: bytes, media_type: str) -> PutResult:
        import botocore.exceptions
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return PutResult(key=key, created=False)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != '404':
                raise
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=media_type)
        return PutResult(key=key, created=True)

    async def read(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response['Body'].read()

    async def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)
