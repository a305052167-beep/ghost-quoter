"""Ingestion (fax image/PDF, email, EDI 840) + line-item extraction (LLM or offline rules)."""
import io, json, os, re, urllib.request
from dataclasses import dataclass, asdict, field

@dataclass
class LineItem:
    description: str; quantity: int; unit: str = "pcs"; buyer_ref: str = ""; sku_hint: str = ""

@dataclass
class RFQ:
    source_format: str; buyer: str = "Unknown Buyer"; reference: str = ""; raw_text: str = ""
    items: list = field(default_factory=list); engine: str = "rules"; edi_meta: dict = field(default_factory=dict)
    def to_dict(self):
        d = asdict(self); return d

def detect_format(filename, data: bytes):
    name = filename.lower()
    head = data[:200].lstrip()
    if head.startswith(b"ISA") or name.endswith((".edi", ".x12", ".840")):
        return "edi"
    if name.endswith(".pdf") or head.startswith(b"%PDF"):
        return "fax"
    if name.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        return "fax"
    return "email"

def ocr(filename, data: bytes):
    """OCR a fax. Uses pdf text layer, else pytesseract if installed, else a 'ghost-ocr' PNG text chunk (demo)."""
    if data.startswith(b"%PDF"):
        from pypdf import PdfReader
        text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
        if text.strip():
            return text
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(data))
    except Exception:
        return ""
    try:
        import pytesseract
        return pytesseract.image_to_string(img)
    except Exception:
        return img.info.get("ghost-ocr", "")

# ---------- EDI X12 840 ----------
def parse_edi_840(text):
    seg_term = text[105] if len(text) > 105 and text.startswith("ISA") else "~"
    segs = [s.strip() for s in text.split(seg_term) if s.strip()]
    rfq = RFQ("edi", raw_text=text)
    elem = "*"
    cur = None
    for s in segs:
        e = s.split(elem)
        tag = e[0]
        if tag == "ISA":
            rfq.edi_meta.update(sender=e[6].strip(), receiver=e[8].strip(), control=e[13].strip())
        elif tag == "GS":
            rfq.edi_meta.update(gs_sender=e[2], gs_receiver=e[3], gs_control=e[6])
        elif tag == "BQT":
            rfq.reference = e[2] if len(e) > 2 else ""
        elif tag == "N1" and len(e) > 2 and e[1] == "BY":
            rfq.buyer = e[2]
        elif tag == "PO1":
            qty = int(float(e[2] or 0)); unit = {"EA": "pcs", "PR": "pair", "ST": "set"}.get(e[3], e[3].lower())
            ids = dict(zip(e[6::2], e[7::2])) if len(e) > 7 else {}
            cur = LineItem("", qty, unit, buyer_ref=ids.get("BP", e[1]), sku_hint=ids.get("VP", ""))
            rfq.items.append(cur)
        elif tag == "PID" and cur is not None:
            cur.description = e[5] if len(e) > 5 else ""
    return rfq

# ---------- rules extractor ----------
QTY_LINE = re.compile(
    r"^\s*(?:(?:item\s*)?\d+[.)]\s*|[-*\u2022]\s*)?(?P<a>.*?)\s*(?:[-:x\u00d7,]\s*|\s)(?:qty[:\s]*)?(?P<q>\d[\d,]*)\s*(?P<u>pcs|pieces|pc|pairs?|prs|sets?|units?|ea)\b\.?\s*(?P<b>.*)$",
    re.I)
QTY_FIRST = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])?\s*(?P<q>\d[\d,]*)\s*(?P<u>pcs|pieces|pc|pairs?|prs|sets?|units?|ea)\b\s*(?:of\s*)?(?P<a>.+)$", re.I)
SKU_RE = re.compile(r"\bTC-[A-Z]{2}-[A-Z0-9]+\b", re.I)

def norm_unit(u):
    u = u.lower()
    return "pair" if u.startswith(("pair", "pr")) else "set" if u.startswith("set") else "pcs"

def rules_extract(text, fmt):
    rfq = RFQ(fmt, raw_text=text)
    m = re.search(r"^(?:from|company|buyer)\s*:\s*(.+)$", text, re.I | re.M)
    if m: rfq.buyer = m.group(1).strip()
    m = re.search(r"(?:rfq|ref(?:erence)?)\s*(?:no\.?|#|number)?\s*[:#]?\s*([A-Z0-9][A-Z0-9-]{3,})", text, re.I)
    if m: rfq.reference = m.group(1)
    for line in text.splitlines():
        if re.match(r"^\s*(from|to|subject|date|tel|fax|page)\s*:", line, re.I):
            continue
        mm = QTY_FIRST.match(line) or QTY_LINE.match(line)
        if not mm: continue
        desc = (mm.group("a") + " " + (mm.groupdict().get("b") or "")).strip(" -:,.")
        if len(desc) < 3: continue
        sku = SKU_RE.search(line)
        rfq.items.append(LineItem(desc, int(mm.group("q").replace(",", "")), norm_unit(mm.group("u")),
                                  sku_hint=sku.group(0).upper() if sku else ""))
    return rfq

# ---------- LLM extractor (OpenAI-compatible) ----------
PROMPT = ("Extract the RFQ from this document. Reply ONLY JSON: {\"buyer\":str,\"reference\":str,"
          "\"items\":[{\"description\":str,\"quantity\":int,\"unit\":\"pcs|pair|set\",\"sku_hint\":str}]}\n\n")

def llm_extract(text, fmt):
    key = os.getenv("GHOST_LLM_API_KEY")
    if not key: return None
    base = os.getenv("GHOST_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    body = json.dumps({"model": os.getenv("GHOST_LLM_MODEL", "gpt-4o-mini"), "temperature": 0,
                       "messages": [{"role": "user", "content": PROMPT + text[:12000]}]}).encode()
    req = urllib.request.Request(base + "/chat/completions", body,
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            content = json.load(r)["choices"][0]["message"]["content"]
        data = json.loads(re.search(r"\{.*\}", content, re.S).group(0))
        rfq = RFQ(fmt, data.get("buyer") or "Unknown Buyer", data.get("reference", ""), text, engine="llm")
        rfq.items = [LineItem(i["description"], int(i["quantity"]), norm_unit(i.get("unit", "pcs")),
                              sku_hint=i.get("sku_hint", "")) for i in data.get("items", [])]
        return rfq
    except Exception:
        return None  # fall back to rules

def ingest(filename, data: bytes):
    fmt = detect_format(filename, data)
    if fmt == "edi":
        return parse_edi_840(data.decode("utf-8", "replace"))
    text = ocr(filename, data) if fmt == "fax" else data.decode("utf-8", "replace")
    return llm_extract(text, fmt) or rules_extract(text, fmt)
