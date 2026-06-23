import uuid
import io
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException
from config import settings

_client: Minio | None = None

MEDIA_TYPES = {
    # images
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/webp": "image",
    "image/heic": "image",
    # video
    "video/mp4": "video",
    "video/quicktime": "video",
    "video/webm": "video",
    "video/x-matroska": "video",
    # audio
    "audio/mpeg": "audio",
    "audio/ogg": "audio",
    "audio/wav": "audio",
    "audio/aac": "audio",
    "audio/webm": "audio",
    # files
    "application/pdf": "file",
    "application/zip": "file",
    "application/octet-stream": "file",
    "text/plain": "file",
    "application/msword": "file",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "file",
}

MAX_SIZES = {
    "image": 10 * 1024 * 1024,   # 10 MB
    "video": 200 * 1024 * 1024,  # 200 MB
    "audio": 50 * 1024 * 1024,   # 50 MB
    "file":  50 * 1024 * 1024,   # 50 MB
}


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False,
        )
    return _client


def ensure_bucket() -> None:
    client = get_client()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)
        # public read policy so URLs are directly accessible
        policy = f'''{{
            "Version":"2012-10-17",
            "Statement":[{{
                "Effect":"Allow",
                "Principal":{{"AWS":["*"]}},
                "Action":["s3:GetObject"],
                "Resource":["arn:aws:s3:::{settings.MINIO_BUCKET}/*"]
            }}]
        }}'''
        client.set_bucket_policy(settings.MINIO_BUCKET, policy)


def classify(content_type: str) -> str:
    kind = MEDIA_TYPES.get(content_type)
    if not kind:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {content_type}")
    return kind


async def upload_file(file: UploadFile) -> dict:
    content_type = file.content_type or "application/octet-stream"
    kind = classify(content_type)

    data = await file.read()
    size = len(data)

    if size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    if size > MAX_SIZES[kind]:
        limit_mb = MAX_SIZES[kind] // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"{kind.capitalize()} exceeds {limit_mb} MB limit")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    object_name = f"{kind}/{uuid.uuid4()}.{ext}" if ext else f"{kind}/{uuid.uuid4()}"

    client = get_client()
    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        io.BytesIO(data),
        length=size,
        content_type=content_type,
    )

    url = f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
    return {"object_name": object_name, "url": url, "kind": kind, "size": size, "filename": file.filename or object_name}


def delete_file(object_name: str) -> None:
    try:
        get_client().remove_object(settings.MINIO_BUCKET, object_name)
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {e}")
