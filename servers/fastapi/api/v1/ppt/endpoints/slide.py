from typing import Annotated, Optional
from copy import deepcopy
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from services.database import get_async_session
from services.image_generation_service import ImageGenerationService
from utils.asset_directory_utils import get_images_directory
from utils.llm_calls.edit_slide import get_edited_slide_content
from utils.llm_calls.edit_slide_html import get_edited_slide_html
from utils.llm_calls.select_slide_type_on_edit import get_slide_layout_from_prompt
from utils.process_slides import process_old_and_new_slides_and_fetch_assets


SLIDE_ROUTER = APIRouter(prefix="/slide", tags=["Slide"])


@SLIDE_ROUTER.post("/edit")
async def edit_slide(
    id: Annotated[uuid.UUID, Body()],
    prompt: Annotated[Optional[str], Body()] = None,
    content_updates: Annotated[Optional[dict], Body()] = None,
    speaker_note: Annotated[Optional[str], Body()] = None,
    sql_session: AsyncSession = Depends(get_async_session),
):
    slide = await sql_session.get(SlideModel, id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    presentation = await sql_session.get(PresentationModel, slide.presentation)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    prompt = (prompt or "").strip()

    if not prompt and not content_updates and speaker_note is None:
        raise HTTPException(status_code=400, detail="No edit operation provided")

    def _apply_shape_level_updates(content: dict, updates: dict):
        merged_content = deepcopy(content)
        for shape_key in sorted(updates.keys()):
            next_value = updates[shape_key]
            previous_value = merged_content.get(shape_key)
            if isinstance(previous_value, dict) and isinstance(next_value, dict):
                merged_content[shape_key] = {**previous_value, **next_value}
            else:
                merged_content[shape_key] = next_value
        return merged_content

    edited_slide_content = slide.content
    slide_layout = slide.layout
    new_assets = []

    if prompt:
        presentation_layout = presentation.get_layout()
        resolved_slide_layout = await get_slide_layout_from_prompt(
            prompt, presentation_layout, slide
        )
        slide_layout = resolved_slide_layout.id

        edited_slide_content = await get_edited_slide_content(
            prompt, slide, presentation.language, resolved_slide_layout
        )

        image_generation_service = ImageGenerationService(get_images_directory())

        # This will mutate edited_slide_content
        new_assets = await process_old_and_new_slides_and_fetch_assets(
            image_generation_service,
            slide.content,
            edited_slide_content,
        )

    if content_updates:
        edited_slide_content = _apply_shape_level_updates(
            edited_slide_content, content_updates
        )

    # Always assign a new unique id to the slide
    slide.id = uuid.uuid4()

    sql_session.add(slide)
    slide.content = edited_slide_content
    slide.layout = slide_layout
    if speaker_note is not None:
        slide.speaker_note = speaker_note
        slide.content["__speaker_note__"] = speaker_note
    else:
        slide.speaker_note = edited_slide_content.get("__speaker_note__", "")
    sql_session.add_all(new_assets)
    await sql_session.commit()

    return slide


@SLIDE_ROUTER.post("/edit-html", response_model=SlideModel)
async def edit_slide_html(
    id: Annotated[uuid.UUID, Body()],
    prompt: Annotated[str, Body()],
    html: Annotated[Optional[str], Body()] = None,
    sql_session: AsyncSession = Depends(get_async_session),
):
    slide = await sql_session.get(SlideModel, id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    html_to_edit = html or slide.html_content
    if not html_to_edit:
        raise HTTPException(status_code=400, detail="No HTML to edit")

    edited_slide_html = await get_edited_slide_html(prompt, html_to_edit)

    # Always assign a new unique id to the slide
    # This is to ensure that the nextjs can track slide updates
    slide.id = uuid.uuid4()

    sql_session.add(slide)
    slide.html_content = edited_slide_html
    await sql_session.commit()

    return slide
