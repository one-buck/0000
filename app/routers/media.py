from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional

from database import get_db, User, Media
from schemas import MediaResponse
from storage import upload_file, delete_file
from utils import get_entity_or_404

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/upload", response_model=MediaResponse, status_code=201)
async def upload_media(
    uploader_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image, video, audio, or file. Returns the stored URL."""
    await get_entity_or_404(db, User, uploader_id, "Uploader not found")

    result = await upload_file(file)

    db_media = Media(
        uploader_id=uploader_id,
        object_name=result["object_name"],
        url=result["url"],
        filename=result["filename"],
        kind=result["kind"],
        size=result["size"],
    )
    db.add(db_media)
    try:
        await db.commit()
        await db.refresh(db_media)
        return db_media
    except SQLAlchemyError as e:
        delete_file(result["object_name"])
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[MediaResponse])
async def list_media(
    uploader_id: Optional[int] = None,
    kind: Optional[str] = Query(None, description="Filter by type: image, video, audio, file"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List uploaded media, optionally filtered by uploader or type."""
    stmt = select(Media)
    if uploader_id is not None:
        stmt = stmt.where(Media.uploader_id == uploader_id)
    if kind is not None:
        if kind not in ("image", "video", "audio", "file"):
            raise HTTPException(status_code=400, detail="kind must be one of: image, video, audio, file")
        stmt = stmt.where(Media.kind == kind)
    stmt = stmt.order_by(Media.uploaded_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(media_id: int, db: AsyncSession = Depends(get_db)):
    return await get_entity_or_404(db, Media, media_id, "Media not found")


@router.delete("/{media_id}")
async def delete_media(
    media_id: int,
    requester_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a media record and its file from MinIO. Only the uploader can delete."""
    media = await get_entity_or_404(db, Media, media_id, "Media not found")
    if media.uploader_id != requester_id:
        raise HTTPException(status_code=403, detail="Only the uploader can delete this file")

    delete_file(media.object_name)
    await db.delete(media)
    try:
        await db.commit()
        return {"detail": "Media deleted"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
