from typing import Optional
import uuid

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class SlideImportMappingModel(SQLModel, table=True):
    __tablename__ = "slide_import_mappings"
    __table_args__ = (
        UniqueConstraint("slide_id", "shape_key", name="uq_slide_import_mapping_slide_shape"),
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    slide_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("slides.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    presentation_id: uuid.UUID = Field(sa_column=Column(nullable=False, index=True))
    slide_index: int = Field(index=True)
    shape_key: str = Field(sa_column=Column(String, nullable=False))
    source_part: str = Field(sa_column=Column(String, nullable=False))
    source_shape_id: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    rel_id: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    media_target: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
