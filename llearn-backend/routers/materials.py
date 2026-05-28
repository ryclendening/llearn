from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.crud import (
    course_material_to_payload,
    create_course_material,
    list_course_materials,
    update_course_material_ingest_result,
)
from db.session import get_db
from vector_db.pipeline import ingest_pdf


router = APIRouter(prefix="/api", tags=["materials"])

UPLOAD_ROOT = Path("uploads/materials")
SUPPORTED_CONTENT_TYPES = {"application/pdf"}


@router.post("/classes/{class_id}/materials")
async def upload_class_material(
    class_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported right now.")

    original_name = Path(file.filename or "material.pdf").name
    material_token = uuid4().hex
    class_dir = UPLOAD_ROOT / class_id
    class_dir.mkdir(parents=True, exist_ok=True)
    storage_path = class_dir / f"{material_token}_{original_name}"
    vector_document_id = f"{class_id}:{material_token}:{original_name}"

    with storage_path.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    try:
        material = create_course_material(
            db,
            lesson_id=class_id,
            filename=original_name,
            content_type=file.content_type,
            storage_path=str(storage_path),
            vector_document_id=vector_document_id,
        )
    except ValueError:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Class not found")

    try:
        chunk_ids = ingest_pdf(
            str(storage_path),
            doc_id=vector_document_id,
            class_id=class_id,
            material_id=material.id,
        )
    except Exception as exc:
        material = update_course_material_ingest_result(
            db,
            material_id=material.id,
            status="failed",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Material was saved, but vector ingestion failed.",
                "material": course_material_to_payload(material),
            },
        ) from exc

    material = update_course_material_ingest_result(
        db,
        material_id=material.id,
        status="ready",
        chunk_count=len(chunk_ids),
    )
    return course_material_to_payload(material)


@router.get("/classes/{class_id}/materials")
async def get_class_materials(class_id: str, db: Session = Depends(get_db)):
    materials = list_course_materials(db, class_id)
    if materials is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"materials": [course_material_to_payload(material) for material in materials]}
