import os
from typing import Any, Literal
import uuid

import aiohttp
from fastapi import HTTPException
from pathvalidate import sanitize_filename

from models.pptx_models import PptxPresentationModel
from models.presentation_and_path import PresentationAndPath
from services.pptx_presentation_creator import PptxPresentationCreator
from services.pptx_roundtrip_service import PptxRoundtripService
from services.temp_file_service import TEMP_FILE_SERVICE
from utils.asset_directory_utils import get_exports_directory


async def export_presentation(
    presentation_id: uuid.UUID, title: str, export_as: Literal["pptx", "pdf"]
) -> PresentationAndPath:
    if export_as == "pptx":
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://localhost/api/presentation_to_pptx_model?id={presentation_id}"
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Failed to get PPTX model: {error_text}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to convert presentation to PPTX model",
                    )
                export_payload: Any = await response.json()

        export_directory = get_exports_directory()
        pptx_path = os.path.join(
            export_directory,
            f"{sanitize_filename(title or str(uuid.uuid4()))}.pptx",
        )

        if _is_pptx_import_roundtrip(export_payload):
            temp_dir = TEMP_FILE_SERVICE.create_temp_dir()
            roundtrip_service = PptxRoundtripService(temp_dir)
            roundtrip_payload = export_payload["roundtrip"]
            roundtrip_service.export_from_import(
                original_pptx_path=roundtrip_payload["original_pptx_path"],
                export_path=pptx_path,
                file_edits=roundtrip_payload.get("file_edits", []),
                relationship_edits=roundtrip_payload.get("relationship_edits", []),
            )
        else:
            pptx_model_data = _extract_pptx_model_payload(export_payload)
            pptx_model = PptxPresentationModel(**pptx_model_data)
            temp_dir = TEMP_FILE_SERVICE.create_temp_dir()
            pptx_creator = PptxPresentationCreator(pptx_model, temp_dir)
            await pptx_creator.create_ppt()
            pptx_creator.save(pptx_path)

        return PresentationAndPath(
            presentation_id=presentation_id,
            path=pptx_path,
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost/api/export-as-pdf",
            json={
                "id": str(presentation_id),
                "title": sanitize_filename(title or str(uuid.uuid4())),
            },
        ) as response:
            response_json = await response.json()

    return PresentationAndPath(
        presentation_id=presentation_id,
        path=response_json["path"],
    )


def _is_pptx_import_roundtrip(export_payload: Any) -> bool:
    if not isinstance(export_payload, dict):
        return False

    roundtrip_payload = export_payload.get("roundtrip")
    return bool(
        roundtrip_payload
        and isinstance(roundtrip_payload, dict)
        and roundtrip_payload.get("original_pptx_path")
        and (
            export_payload.get("is_imported_pptx") is True
            or roundtrip_payload.get("is_imported_pptx") is True
        )
    )


def _extract_pptx_model_payload(export_payload: Any) -> Any:
    if isinstance(export_payload, dict) and "pptx_model" in export_payload:
        return export_payload["pptx_model"]
    return export_payload
