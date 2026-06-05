from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from db.crud import (
    create_extracted_examples,
    update_course_material_extraction_result,
    update_course_material_ingest_result,
)
from db.models import CourseMaterial
from examples.extraction import extract_example_problems
from vector_db.ingestion import ingest_pdf


@dataclass(frozen=True)
class MaterialProcessingResult:
    materials: list[CourseMaterial]
    extracted_example_count: int
    extraction_error: str | None


class VectorIngestionError(Exception):
    def __init__(self, message: str, materials: list[CourseMaterial]):
        super().__init__(message)
        self.materials = materials


def process_materials(
    db: Session,
    *,
    storage_path: str,
    materials: list[CourseMaterial],
) -> MaterialProcessingResult:
    ingested_materials = _ingest_materials(db, storage_path=storage_path, materials=materials)
    return _extract_examples(db, storage_path=storage_path, materials=ingested_materials)


def _ingest_materials(
    db: Session,
    *,
    storage_path: str,
    materials: list[CourseMaterial],
) -> list[CourseMaterial]:
    completed = []
    try:
        for material in materials:
            chunk_ids = ingest_pdf(
                storage_path,
                doc_id=material.vector_document_id,
                class_id=material.lesson_id,
                material_id=material.id,
            )
            completed.append(
                update_course_material_ingest_result(
                    db,
                    material_id=material.id,
                    status="ready",
                    chunk_count=len(chunk_ids),
                )
            )
    except Exception as exc:
        completed_ids = {material.id for material in completed}
        for material in materials:
            if material.id not in completed_ids:
                update_course_material_ingest_result(
                    db,
                    material_id=material.id,
                    status="failed",
                    error_message=str(exc),
                )
        raise VectorIngestionError(str(exc), materials) from exc
    return completed


def _extract_examples(
    db: Session,
    *,
    storage_path: str,
    materials: list[CourseMaterial],
) -> MaterialProcessingResult:
    extracted_count = 0
    material_ids = [material.id for material in materials]
    try:
        extracted_examples = extract_example_problems(storage_path)
        completed = []
        for material_id in material_ids:
            created_examples = create_extracted_examples(
                db,
                material_id=material_id,
                examples=extracted_examples,
            )
            extracted_count += len(created_examples)
            completed.append(
                update_course_material_extraction_result(
                    db,
                    material_id=material_id,
                    status="ready",
                )
            )
        return MaterialProcessingResult(completed, extracted_count, None)
    except Exception as exc:
        db.rollback()
        error = str(exc)
        failed = [
            update_course_material_extraction_result(
                db,
                material_id=material_id,
                status="failed",
                error_message=error,
            )
            for material_id in material_ids
        ]
        return MaterialProcessingResult(failed, 0, error)
