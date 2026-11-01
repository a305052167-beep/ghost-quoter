from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.catalog import load_catalog, match
from app.extract import ingest, detect_format, parse_edi_840
from app.quote import build_quote, edi_843, email_reply, quotation_pdf

S = Path(__file__).resolve().parent.parent / "samples"
CAT = load_catalog()

@pytest.fixture(autouse=True)
def no_llm(monkeypatch): monkeypatch.delenv("GHOST_LLM_API_KEY", raising=False)

def test_catalog_size(): assert 25 <= len(CAT) <= 35

def test_match_by_keywords():
    p, c = match("35mm soft close hinge full overlay", CAT); assert p.sku == "TC-HG-3501" and c >= 0.6

def test_match_sku_hint(): assert match("whatever", CAT, "TC-LK-CAM")[0].sku == "TC-LK-CAM"

def test_no_match(): assert match("pumpkin door knocker", CAT)[0] is None

def test_detect():
    assert detect_format("a.edi", b"ISA*") == "edi" and detect_format("a.pdf", b"%PDF") == "fax"
    assert detect_format("a.txt", b"hello") == "email"

def test_email_extract():
    r = ingest("rfq_email.txt", (S / "rfq_email.txt").read_bytes())
    assert r.reference == "NW-2026-1031" and len(r.items) == 6
    assert r.items[0].quantity == 5000 and r.items[1].unit == "pair"
    q = build_quote(r, CAT); skus = [l["sku"] for l in q["lines"]]
    assert skus[:5] == ["TC-HG-3501", "TC-DS-4518", "TC-HD-T128", "TC-KN-030", "TC-GS-100"] and skus[5] == ""

def test_edi_roundtrip():
    r = parse_edi_840((S / "rfq_840.edi").read_text())
    assert r.reference == "RFQ-EDI-7781" and len(r.items) == 3 and r.items[1].unit == "pair"
    q = build_quote(r, CAT); out = edi_843(q)
    assert "ST*843*0001" in out and "VP*TC-DS-UM21" in out and out.strip().endswith("~")
    assert "BQR*00*" in out and "RFQ-EDI-7781" in out

@pytest.mark.parametrize("name", ["rfq_fax.pdf", "rfq_fax.png"])
def test_fax(name):
    r = ingest(name, (S / name).read_bytes())
    assert r.source_format == "fax" and len(r.items) == 5 and r.reference == "HH-RFQ-1313"
    q = build_quote(r, CAT); assert all(l["sku"] for l in q["lines"])

def test_pdf_and_email_reply():
    q = build_quote(ingest("e.txt", (S / "rfq_email.txt").read_bytes()), CAT)
    assert quotation_pdf(q).startswith(b"%PDF") and "TOTAL: USD" in email_reply(q)

def test_web_flow():
    c = TestClient(app); assert c.get("/").status_code == 200
    for f in ["rfq_email.txt", "rfq_840.edi", "rfq_fax.pdf"]:
        r = c.post("/api/quote", files={"file": (f, (S / f).read_bytes())}); assert r.status_code == 200
        qid = r.json()["id"]
        assert c.get(f"/quote/{qid}/pdf").content.startswith(b"%PDF")
        assert c.get(f"/quote/{qid}/reply").status_code == 200
    assert c.post("/upload", files={"file": ("rfq_email.txt", (S / "rfq_email.txt").read_bytes())}).status_code == 200
    assert c.get("/quote/nope/pdf").status_code == 404
