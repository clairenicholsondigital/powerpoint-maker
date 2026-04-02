from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PptxPartSummary(BaseModel):
    path: str
    name: str


class PptxColorEntry(BaseModel):
    key: str
    value: str


class PptxFontScheme(BaseModel):
    name: Optional[str] = None
    major_latin: Optional[str] = None
    minor_latin: Optional[str] = None


class PptxColorScheme(BaseModel):
    name: Optional[str] = None
    colors: List[PptxColorEntry] = Field(default_factory=list)


class PptxPlaceholderDefault(BaseModel):
    part_path: str
    shape_id: Optional[str] = None
    placeholder_type: Optional[str] = None
    placeholder_index: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None


class PptxMasterObject(BaseModel):
    part_path: str
    object_id: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None


class PptxMasterGovernanceState(BaseModel):
    slide_masters: List[PptxPartSummary] = Field(default_factory=list)
    slide_layouts: List[PptxPartSummary] = Field(default_factory=list)
    themes: List[PptxPartSummary] = Field(default_factory=list)
    font_schemes: Dict[str, PptxFontScheme] = Field(default_factory=dict)
    color_schemes: Dict[str, PptxColorScheme] = Field(default_factory=dict)
    placeholder_defaults: List[PptxPlaceholderDefault] = Field(default_factory=list)
    master_objects: List[PptxMasterObject] = Field(default_factory=list)


class FontSchemeUpdate(BaseModel):
    theme_path: str
    name: Optional[str] = None
    major_latin: Optional[str] = None
    minor_latin: Optional[str] = None


class ColorSchemeUpdate(BaseModel):
    theme_path: str
    name: Optional[str] = None
    colors: Dict[str, str] = Field(default_factory=dict)


class PlaceholderUpdate(BaseModel):
    part_path: str
    shape_id: Optional[str] = None
    placeholder_type: Optional[str] = None
    placeholder_index: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None


class MasterObjectUpdate(BaseModel):
    part_path: str
    object_id: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None


class PptxMasterGovernancePatchRequest(BaseModel):
    font_schemes: List[FontSchemeUpdate] = Field(default_factory=list)
    color_schemes: List[ColorSchemeUpdate] = Field(default_factory=list)
    placeholder_defaults: List[PlaceholderUpdate] = Field(default_factory=list)
    master_objects: List[MasterObjectUpdate] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
