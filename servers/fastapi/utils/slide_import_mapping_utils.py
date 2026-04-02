from typing import Any, Iterable, List

from models.sql.slide import SlideModel
from models.sql.slide_import_mapping import SlideImportMappingModel


IMPORT_MAPPINGS_CONTENT_KEY = "__import_mappings__"
IMPORT_MAPPINGS_PROPERTIES_KEY = "import_mappings"


def build_slide_import_mappings(slides: Iterable[SlideModel]) -> List[SlideImportMappingModel]:
    mappings: List[SlideImportMappingModel] = []

    for slide in slides:
        raw_mappings: Any = None

        if isinstance(slide.properties, dict):
            raw_mappings = slide.properties.get(IMPORT_MAPPINGS_PROPERTIES_KEY)

        if raw_mappings is None and isinstance(slide.content, dict):
            raw_mappings = slide.content.get(IMPORT_MAPPINGS_CONTENT_KEY)

        if not isinstance(raw_mappings, list):
            continue

        for item in raw_mappings:
            if not isinstance(item, dict):
                continue

            shape_key = item.get("shape_key")
            source_part = item.get("source_part")
            if not shape_key or not source_part:
                continue

            mappings.append(
                SlideImportMappingModel(
                    slide_id=slide.id,
                    presentation_id=slide.presentation,
                    slide_index=slide.index,
                    shape_key=str(shape_key),
                    source_part=str(source_part),
                    source_shape_id=_to_optional_string(item.get("source_shape_id")),
                    rel_id=_to_optional_string(item.get("rel_id")),
                    media_target=_to_optional_string(item.get("media_target")),
                )
            )

    return mappings


def _to_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value)
    return value if value else None
