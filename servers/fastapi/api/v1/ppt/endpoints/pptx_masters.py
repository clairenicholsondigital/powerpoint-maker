from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from constants.documents import POWERPOINT_TYPES
from models.pptx_master_models import PptxMasterGovernancePatchRequest
from services.pptx_master_service import PptxMasterGovernanceService

PPTX_MASTER_ROUTER = APIRouter(prefix="/pptx-masters", tags=["PPTX Master Governance"])


@PPTX_MASTER_ROUTER.post("/inspect")
async def inspect_pptx_master_governance(
    pptx_file: UploadFile = File(..., description="PPTX file to inspect master/theme/layout parts")
):
    if pptx_file.content_type not in POWERPOINT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Expected PPTX file, got {pptx_file.content_type}")

    content = await pptx_file.read()
    archive = PptxMasterGovernanceService.load_pptx(content)
    state = PptxMasterGovernanceService.inspect(archive)

    return JSONResponse(
        {
            "success": True,
            "milestone": "master_template_governance",
            "round_trip_dependency": "stable_slide_level_round_trip",
            "state": state.model_dump(),
        }
    )


@PPTX_MASTER_ROUTER.post("/apply")
async def apply_pptx_master_governance_patch(
    pptx_file: UploadFile = File(..., description="PPTX file to patch"),
    patch: str = Form(..., description="JSON payload matching PptxMasterGovernancePatchRequest"),
):
    if pptx_file.content_type not in POWERPOINT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Expected PPTX file, got {pptx_file.content_type}")

    patch_model = PptxMasterGovernancePatchRequest.model_validate_json(patch)

    content = await pptx_file.read()
    archive = PptxMasterGovernanceService.load_pptx(content)
    updated_archive = PptxMasterGovernanceService.apply_patch(archive, patch_model)
    output = PptxMasterGovernanceService.dump_pptx(updated_archive)

    return Response(
        content=output,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": "attachment; filename=master-governance-updated.pptx"},
    )
