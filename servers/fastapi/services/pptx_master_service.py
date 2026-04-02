import io
import posixpath
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from models.pptx_master_models import (
    ColorSchemeUpdate,
    FontSchemeUpdate,
    MasterObjectUpdate,
    PlaceholderUpdate,
    PptxColorEntry,
    PptxColorScheme,
    PptxMasterGovernancePatchRequest,
    PptxMasterGovernanceState,
    PptxMasterObject,
    PptxPartSummary,
    PptxPlaceholderDefault,
    PptxFontScheme,
)

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"

NS = {"a": A_NS, "p": P_NS}


@dataclass
class PptxArchive:
    files: Dict[str, bytes]


def _norm(path: str) -> str:
    return posixpath.normpath(path).lstrip("/")


def _parse_xml(content: bytes) -> Optional[ET.Element]:
    try:
        return ET.fromstring(content)
    except ET.ParseError:
        return None


def _first_text(root: ET.Element, xpath: str) -> Optional[str]:
    node = root.find(xpath, NS)
    return node.text.strip() if node is not None and node.text else None


def _shape_selector(root: ET.Element, part: str, shape_id: Optional[str], placeholder_type: Optional[str], placeholder_index: Optional[str]) -> Optional[ET.Element]:
    for sp in root.findall(".//p:sp", NS):
        c_nv_pr = sp.find("./p:nvSpPr/p:cNvPr", NS)
        if shape_id and (c_nv_pr is None or c_nv_pr.attrib.get("id") != shape_id):
            continue
        ph = sp.find("./p:nvSpPr/p:nvPr/p:ph", NS)
        if placeholder_type and (ph is None or ph.attrib.get("type") != placeholder_type):
            continue
        if placeholder_index and (ph is None or ph.attrib.get("idx") != placeholder_index):
            continue
        return sp
    return None


class PptxMasterGovernanceService:
    @staticmethod
    def load_pptx(content: bytes) -> PptxArchive:
        with zipfile.ZipFile(io.BytesIO(content), "r") as zf:
            files = {name: zf.read(name) for name in zf.namelist()}
        return PptxArchive(files=files)

    @staticmethod
    def dump_pptx(archive: PptxArchive) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, payload in archive.files.items():
                zf.writestr(name, payload)
        return buffer.getvalue()

    @staticmethod
    def inspect(archive: PptxArchive) -> PptxMasterGovernanceState:
        masters = _collect_parts(archive.files.keys(), "ppt/slideMasters/")
        layouts = _collect_parts(archive.files.keys(), "ppt/slideLayouts/")
        themes = _collect_parts(archive.files.keys(), "ppt/theme/")

        font_schemes: Dict[str, PptxFontScheme] = {}
        color_schemes: Dict[str, PptxColorScheme] = {}

        for theme in themes:
            root = _parse_xml(archive.files[theme.path])
            if root is None:
                continue

            font_scheme_node = root.find(".//a:themeElements/a:fontScheme", NS)
            if font_scheme_node is not None:
                font_schemes[theme.path] = PptxFontScheme(
                    name=font_scheme_node.attrib.get("name"),
                    major_latin=_first_typeface(font_scheme_node, "./a:majorFont/a:latin"),
                    minor_latin=_first_typeface(font_scheme_node, "./a:minorFont/a:latin"),
                )

            color_scheme_node = root.find(".//a:themeElements/a:clrScheme", NS)
            if color_scheme_node is not None:
                entries: List[PptxColorEntry] = []
                for color_node in list(color_scheme_node):
                    color_value = _extract_color_value(color_node)
                    entries.append(PptxColorEntry(key=_local_name(color_node.tag), value=color_value or ""))
                color_schemes[theme.path] = PptxColorScheme(
                    name=color_scheme_node.attrib.get("name"),
                    colors=entries,
                )

        placeholder_defaults: List[PptxPlaceholderDefault] = []
        master_objects: List[PptxMasterObject] = []

        for part in [*masters, *layouts]:
            root = _parse_xml(archive.files[part.path])
            if root is None:
                continue

            for sp in root.findall(".//p:sp", NS):
                c_nv_pr = sp.find("./p:nvSpPr/p:cNvPr", NS)
                ph = sp.find("./p:nvSpPr/p:nvPr/p:ph", NS)
                text = _extract_shape_text(sp)
                item = PptxMasterObject(
                    part_path=part.path,
                    object_id=c_nv_pr.attrib.get("id") if c_nv_pr is not None else None,
                    name=c_nv_pr.attrib.get("name") if c_nv_pr is not None else None,
                    text=text,
                )
                master_objects.append(item)

                if ph is not None:
                    placeholder_defaults.append(
                        PptxPlaceholderDefault(
                            part_path=part.path,
                            shape_id=item.object_id,
                            placeholder_type=ph.attrib.get("type"),
                            placeholder_index=ph.attrib.get("idx"),
                            name=item.name,
                            text=text,
                        )
                    )

        return PptxMasterGovernanceState(
            slide_masters=masters,
            slide_layouts=layouts,
            themes=themes,
            font_schemes=font_schemes,
            color_schemes=color_schemes,
            placeholder_defaults=placeholder_defaults,
            master_objects=master_objects,
        )

    @staticmethod
    def apply_patch(archive: PptxArchive, patch: PptxMasterGovernancePatchRequest) -> PptxArchive:
        for update in patch.font_schemes:
            _apply_font_scheme_update(archive, update)
        for update in patch.color_schemes:
            _apply_color_scheme_update(archive, update)
        for update in patch.placeholder_defaults:
            _apply_placeholder_update(archive, update)
        for update in patch.master_objects:
            _apply_master_object_update(archive, update)
        return archive


def _collect_parts(paths: Iterable[str], prefix: str) -> List[PptxPartSummary]:
    results = [
        PptxPartSummary(path=path, name=posixpath.basename(path))
        for path in sorted(paths)
        if path.startswith(prefix) and path.endswith(".xml")
    ]
    return results


def _first_typeface(root: ET.Element, xpath: str) -> Optional[str]:
    node = root.find(xpath, NS)
    if node is None:
        return None
    return node.attrib.get("typeface")


def _extract_color_value(color_node: ET.Element) -> Optional[str]:
    for child in list(color_node):
        val = child.attrib.get("val") or child.attrib.get("lastClr")
        if val:
            return val
    return None


def _local_name(tag: str) -> str:
    return tag.split("}")[-1]


def _extract_shape_text(shape: ET.Element) -> Optional[str]:
    text_nodes = shape.findall(".//a:t", NS)
    text_chunks = [t.text for t in text_nodes if t.text]
    return "\n".join(text_chunks) if text_chunks else None


def _write_xml(archive: PptxArchive, part_path: str, root: ET.Element) -> None:
    archive.files[_norm(part_path)] = ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _apply_font_scheme_update(archive: PptxArchive, update: FontSchemeUpdate) -> None:
    part_path = _norm(update.theme_path)
    if part_path not in archive.files:
        return
    root = _parse_xml(archive.files[part_path])
    if root is None:
        return

    font_scheme = root.find(".//a:themeElements/a:fontScheme", NS)
    if font_scheme is None:
        return

    if update.name is not None:
        font_scheme.set("name", update.name)
    if update.major_latin is not None:
        node = font_scheme.find("./a:majorFont/a:latin", NS)
        if node is not None:
            node.set("typeface", update.major_latin)
    if update.minor_latin is not None:
        node = font_scheme.find("./a:minorFont/a:latin", NS)
        if node is not None:
            node.set("typeface", update.minor_latin)

    _write_xml(archive, part_path, root)


def _apply_color_scheme_update(archive: PptxArchive, update: ColorSchemeUpdate) -> None:
    part_path = _norm(update.theme_path)
    if part_path not in archive.files:
        return
    root = _parse_xml(archive.files[part_path])
    if root is None:
        return

    clr_scheme = root.find(".//a:themeElements/a:clrScheme", NS)
    if clr_scheme is None:
        return
    if update.name is not None:
        clr_scheme.set("name", update.name)

    color_lookup = {_local_name(node.tag): node for node in list(clr_scheme)}
    for key, value in update.colors.items():
        node = color_lookup.get(key)
        if node is None:
            continue
        child = list(node)[0] if len(list(node)) > 0 else None
        if child is None:
            continue
        if "val" in child.attrib:
            child.set("val", value)
        elif "lastClr" in child.attrib:
            child.set("lastClr", value)

    _write_xml(archive, part_path, root)


def _apply_placeholder_update(archive: PptxArchive, update: PlaceholderUpdate) -> None:
    part_path = _norm(update.part_path)
    if part_path not in archive.files:
        return
    root = _parse_xml(archive.files[part_path])
    if root is None:
        return

    shape = _shape_selector(root, part_path, update.shape_id, update.placeholder_type, update.placeholder_index)
    if shape is None:
        return

    c_nv_pr = shape.find("./p:nvSpPr/p:cNvPr", NS)
    if c_nv_pr is not None and update.name is not None:
        c_nv_pr.set("name", update.name)

    if update.text is not None:
        for t in shape.findall(".//a:t", NS):
            t.text = update.text

    _write_xml(archive, part_path, root)


def _apply_master_object_update(archive: PptxArchive, update: MasterObjectUpdate) -> None:
    _apply_placeholder_update(
        archive,
        PlaceholderUpdate(
            part_path=update.part_path,
            shape_id=update.object_id,
            name=update.name,
            text=update.text,
        ),
    )
