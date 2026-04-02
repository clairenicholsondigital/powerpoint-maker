import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
import xml.etree.ElementTree as ET


class PptxRoundtripService:
    """Rebuild a PPTX by patching an imported package with persisted edits."""

    def __init__(self, working_dir: str):
        self.working_dir = Path(working_dir)
        self.unpack_dir = self.working_dir / "pptx_roundtrip"

    def export_from_import(
        self,
        *,
        original_pptx_path: str,
        export_path: str,
        file_edits: Iterable[Dict[str, Any]],
        relationship_edits: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> str:
        self._unpack_original_package(original_pptx_path)
        self._apply_file_edits(file_edits)
        self._apply_relationship_edits(relationship_edits or [])
        self._repack_to_export_path(export_path)
        return export_path

    def _unpack_original_package(self, original_pptx_path: str) -> None:
        if not os.path.exists(original_pptx_path):
            raise FileNotFoundError(f"Original PPTX does not exist: {original_pptx_path}")

        if self.unpack_dir.exists():
            shutil.rmtree(self.unpack_dir)
        self.unpack_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(original_pptx_path, "r") as original_package:
            original_package.extractall(self.unpack_dir)

    def _apply_file_edits(self, file_edits: Iterable[Dict[str, Any]]) -> None:
        for edit in file_edits:
            package_path = edit["package_path"]
            resolved_path = self.unpack_dir / package_path
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            edit_type = edit.get("edit_type", "xml_replace")
            if edit_type == "xml_replace":
                xml_content = edit.get("xml_content")
                if xml_content is None:
                    continue
                resolved_path.write_text(xml_content, encoding="utf-8")
            elif edit_type == "text_replace":
                target_text = edit.get("target_text")
                replacement_text = edit.get("replacement_text")
                if target_text is None or replacement_text is None:
                    continue
                current_content = resolved_path.read_text(encoding="utf-8")
                resolved_path.write_text(
                    current_content.replace(target_text, replacement_text),
                    encoding="utf-8",
                )
            elif edit_type == "binary_replace":
                source_file_path = edit.get("source_file_path")
                if not source_file_path:
                    continue
                shutil.copyfile(source_file_path, resolved_path)

    def _apply_relationship_edits(
        self, relationship_edits: Iterable[Dict[str, Any]]
    ) -> None:
        for relationship_edit in relationship_edits:
            rels_path = relationship_edit.get("rels_path")
            if not rels_path:
                continue

            resolved_rels_path = self.unpack_dir / rels_path
            if not resolved_rels_path.exists():
                continue

            xml_tree = ET.parse(resolved_rels_path)
            root = xml_tree.getroot()

            updates = relationship_edit.get("updates", [])
            for update in updates:
                relationship_id = update.get("id")
                if not relationship_id:
                    continue

                relationship_node = self._find_relationship_node(root, relationship_id)
                if relationship_node is None:
                    continue

                target = update.get("target")
                target_mode = update.get("target_mode")
                relationship_type = update.get("type")

                if target is not None:
                    relationship_node.set("Target", target)
                if target_mode is not None:
                    relationship_node.set("TargetMode", target_mode)
                if relationship_type is not None:
                    relationship_node.set("Type", relationship_type)

            xml_tree.write(
                resolved_rels_path,
                encoding="utf-8",
                xml_declaration=True,
            )

    def _find_relationship_node(
        self, root: ET.Element, relationship_id: str
    ) -> Optional[ET.Element]:
        for node in root.findall("{*}Relationship"):
            if node.attrib.get("Id") == relationship_id:
                return node
        return None

    def _repack_to_export_path(self, export_path: str) -> None:
        with zipfile.ZipFile(export_path, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for file_path in self.unpack_dir.rglob("*"):
                if file_path.is_file():
                    output.write(file_path, file_path.relative_to(self.unpack_dir))
