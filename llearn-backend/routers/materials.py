from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from db.crud import (
    count_course_materials_with_storage_path,
    course_material_to_payload,
    create_course_material,
    delete_course_material,
    get_course_material,
    get_lesson,
    list_course_materials,
)
from db.session import get_db
from services.material_processing import VectorIngestionError, process_materials
from vector_db.vector_store import get_vector_db


router = APIRouter(prefix="/api", tags=["materials"])

UPLOAD_ROOT = Path("uploads/materials")
SUPPORTED_CONTENT_TYPES = {"application/pdf"}


@router.post("/classes/{class_id}/materials")
async def upload_class_material(
    class_id: str,
    file: UploadFile = File(...),
    class_ids: list[str] | None = Form(default=None),
    db: Session = Depends(get_db),
):
    selected_class_ids = _normalize_class_ids(class_ids or [class_id])
    result = await _upload_material_for_classes(file, selected_class_ids, db)
    if class_ids is None and len(result["materials"]) == 1:
        payload = result["materials"][0]
        payload["extracted_example_count"] = result["extracted_example_count"]
        payload["extraction_error"] = result["extraction_error"]
        return payload
    return result


@router.post("/materials")
async def upload_material(
    file: UploadFile = File(...),
    class_ids: list[str] = Form(...),
    db: Session = Depends(get_db),
):
    selected_class_ids = _normalize_class_ids(class_ids)
    return await _upload_material_for_classes(file, selected_class_ids, db)


def _normalize_class_ids(class_ids: list[str]) -> list[str]:
    selected_class_ids = []
    for class_id in class_ids:
        clean_id = class_id.strip()
        if clean_id and clean_id not in selected_class_ids:
            selected_class_ids.append(clean_id)
    if not selected_class_ids:
        raise HTTPException(status_code=400, detail="Select at least one class.")
    return selected_class_ids


async def _upload_material_for_classes(
    file: UploadFile,
    class_ids: list[str],
    db: Session,
):
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported right now.")
    missing_class_ids = [class_id for class_id in class_ids if not get_lesson(db, class_id)]
    if missing_class_ids:
        raise HTTPException(status_code=404, detail=f"Class not found: {', '.join(missing_class_ids)}")

    original_name = Path(file.filename or "material.pdf").name
    material_token = uuid4().hex
    storage_dir = UPLOAD_ROOT / "shared"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / f"{material_token}_{original_name}"

    with storage_path.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    materials = []
    try:
        for class_id in class_ids:
            vector_document_id = f"{class_id}:{material_token}:{original_name}"
            materials.append(
                create_course_material(
                    db,
                    lesson_id=class_id,
                    filename=original_name,
                    content_type=file.content_type,
                    storage_path=str(storage_path),
                    vector_document_id=vector_document_id,
                )
            )
    except ValueError as exc:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Class not found") from exc

    try:
        result = process_materials(db, storage_path=str(storage_path), materials=materials)
    except VectorIngestionError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Material was saved, but vector ingestion failed.",
                "materials": [course_material_to_payload(material) for material in exc.materials],
            },
        ) from exc

    return {
        "materials": [course_material_to_payload(material) for material in result.materials],
        "filename": original_name,
        "class_ids": class_ids,
        "chunk_count": sum(material.chunk_count for material in result.materials),
        "extracted_example_count": result.extracted_example_count,
        "extraction_error": result.extraction_error,
    }


@router.get("/classes/{class_id}/materials")
async def get_class_materials(class_id: str, db: Session = Depends(get_db)):
    materials = list_course_materials(db, class_id)
    if materials is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"materials": [course_material_to_payload(material) for material in materials]}


@router.delete("/materials/{material_id}")
async def remove_material(material_id: int, db: Session = Depends(get_db)):
    material = get_course_material(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")

    storage_path = material.storage_path
    vector_document_id = material.vector_document_id
    payload = course_material_to_payload(material)

    if material.chunk_count > 0:
        vector_db = get_vector_db()
        try:
            vector_db.delete_by_material_id(material_id)
        except Exception as exc:
            try:
                vector_db.delete_by_document_id(vector_document_id)
            except Exception:
                raise HTTPException(status_code=502, detail="Failed to delete material chunks from the vector store.") from exc
        finally:
            vector_db.close()

    deleted = delete_course_material(db, material_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Material not found")

    if count_course_materials_with_storage_path(db, storage_path) == 0:
        Path(storage_path).unlink(missing_ok=True)

    return {"message": "Material deleted", "material": payload}


@router.get("/materials/{material_id}/file")
async def get_material_file(material_id: int, db: Session = Depends(get_db)):
    material = get_course_material(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")

    storage_path = Path(material.storage_path)
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Material file not found")

    return FileResponse(
        storage_path,
        media_type=material.content_type or "application/pdf",
        filename=material.filename,
        content_disposition_type="inline",
    )
