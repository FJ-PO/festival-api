"""Biblioteca de medios: subida de imágenes para carteles, portadas y artistas."""

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select

from app.core.config import settings
from app.core.deps import AdminUser, DbSession, ManagerUser
from app.models import Media
from app.schemas.cms import MediaRead, MediaUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/media", tags=["CMS · Medios"])

MAX_UPLOAD_BYTES = 8 * 1024 * 1024

# Se comprueba la firma real del archivo, no solo la extensión o el Content-Type que manda el cliente.
# SVG queda fuera a propósito: puede llevar JavaScript y se serviría desde el mismo origen.
SIGNATURES = {
    "image/jpeg": (".jpg", [b"\xff\xd8\xff"]),
    "image/png": (".png", [b"\x89PNG\r\n\x1a\n"]),
    "image/gif": (".gif", [b"GIF87a", b"GIF89a"]),
    "image/webp": (".webp", [b"RIFF"]),
    "application/pdf": (".pdf", [b"%PDF-"]),
}


def detect_type(head: bytes) -> tuple[str, str] | None:
    for content_type, (ext, magics) in SIGNATURES.items():
        if any(head.startswith(m) for m in magics):
            if content_type == "image/webp" and head[8:12] != b"WEBP":
                continue
            return content_type, ext
    return None


def upload_path() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.get("", response_model=Page[MediaRead])
def list_media(
    db: DbSession,
    _: ManagerUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 48,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    total = db.scalar(select(func.count(Media.id)))
    items = db.scalars(select(Media).order_by(Media.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
async def upload_media(
    db: DbSession,
    user: ManagerUser,
    file: Annotated[UploadFile, File(description="JPG, PNG, GIF, WEBP o PDF (máx. 8 MB)")],
    alt: Annotated[str | None, Form(max_length=255)] = None,
):
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "El archivo supera los 8 MB")
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El archivo está vacío")
    detected = detect_type(data[:16])
    if detected is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Formato no permitido (JPG, PNG, GIF, WEBP o PDF)")
    content_type, ext = detected
    filename = f"{uuid.uuid4().hex}{ext}"
    (upload_path() / filename).write_bytes(data)
    media = Media(
        filename=filename,
        original_name=(file.filename or filename)[:255],
        content_type=content_type,
        size=len(data),
        alt=alt,
        uploaded_by_id=user.id,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.patch("/{media_id}", response_model=MediaRead)
def update_media(media_id: int, data: MediaUpdate, db: DbSession, _: ManagerUser):
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    media.alt = data.alt
    db.commit()
    db.refresh(media)
    return media


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(media_id: int, db: DbSession, _: AdminUser):
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    (upload_path() / media.filename).unlink(missing_ok=True)
    db.delete(media)
    db.commit()
