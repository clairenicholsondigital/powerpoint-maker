import io
import zipfile

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def _build_sample_pptx() -> bytes:
    payload = {
        "[Content_Types].xml": """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='xml' ContentType='application/xml'/>
</Types>""",
        "ppt/theme/theme1.xml": """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<a:theme xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main' name='Office Theme'>
  <a:themeElements>
    <a:clrScheme name='Office'>
      <a:dk1><a:srgbClr val='111111'/></a:dk1>
      <a:lt1><a:srgbClr val='FFFFFF'/></a:lt1>
      <a:accent1><a:srgbClr val='4472C4'/></a:accent1>
    </a:clrScheme>
    <a:fontScheme name='Office'>
      <a:majorFont><a:latin typeface='Calibri'/></a:majorFont>
      <a:minorFont><a:latin typeface='Calibri Light'/></a:minorFont>
    </a:fontScheme>
  </a:themeElements>
</a:theme>""",
        "ppt/slideMasters/slideMaster1.xml": """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<p:sldMaster xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main' xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'>
  <p:cSld><p:spTree>
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id='2' name='Title Placeholder'/>
        <p:cNvSpPr/><p:nvPr><p:ph type='title' idx='0'/></p:nvPr>
      </p:nvSpPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>Old title</a:t></a:r></a:p></p:txBody>
    </p:sp>
  </p:spTree></p:cSld>
</p:sldMaster>""",
        "ppt/slideLayouts/slideLayout1.xml": """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<p:sldLayout xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main' xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'>
  <p:cSld><p:spTree/></p:cSld>
</p:sldLayout>""",
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, value in payload.items():
            zf.writestr(name, value)
    return buf.getvalue()


def test_inspect_and_apply_master_governance():
    pptx_bytes = _build_sample_pptx()

    inspect_response = client.post(
        "/api/v1/ppt/pptx-masters/inspect",
        files={"pptx_file": ("sample.pptx", io.BytesIO(pptx_bytes), "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
    )
    assert inspect_response.status_code == 200
    inspect_data = inspect_response.json()
    assert inspect_data["success"] is True
    assert inspect_data["state"]["themes"][0]["path"] == "ppt/theme/theme1.xml"
    assert inspect_data["state"]["font_schemes"]["ppt/theme/theme1.xml"]["major_latin"] == "Calibri"

    patch = {
        "font_schemes": [{"theme_path": "ppt/theme/theme1.xml", "major_latin": "Aptos", "minor_latin": "Inter"}],
        "color_schemes": [{"theme_path": "ppt/theme/theme1.xml", "colors": {"accent1": "FF0000"}}],
        "placeholder_defaults": [
            {
                "part_path": "ppt/slideMasters/slideMaster1.xml",
                "shape_id": "2",
                "placeholder_type": "title",
                "placeholder_index": "0",
                "text": "New title",
            }
        ],
    }

    apply_response = client.post(
        "/api/v1/ppt/pptx-masters/apply",
        files={"pptx_file": ("sample.pptx", io.BytesIO(pptx_bytes), "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
        data={"patch": __import__('json').dumps(patch)},
    )
    assert apply_response.status_code == 200

    with zipfile.ZipFile(io.BytesIO(apply_response.content), "r") as zf:
        theme_xml = zf.read("ppt/theme/theme1.xml").decode("utf-8")
        master_xml = zf.read("ppt/slideMasters/slideMaster1.xml").decode("utf-8")

    assert "Aptos" in theme_xml
    assert "Inter" in theme_xml
    assert "FF0000" in theme_xml
    assert "New title" in master_xml
