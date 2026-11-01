import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .catalog import load_catalog
from .extract import ingest
from .quote import build_quote, quotation_pdf, fax_cover_pdf, email_reply, edi_843

BASE = Path(__file__).parent
app = FastAPI(title="Ghost Quoter 幽灵报价员")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
tpl = Jinja2Templates(directory=BASE / "templates")
QUOTES: dict = {}
CATALOG = load_catalog()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return tpl.TemplateResponse(request, "index.html", {"catalog_size": len(CATALOG)})

def _process(name, data):
    if not data: raise HTTPException(400, "Empty file")
    rfq = ingest(name, data)
    q = build_quote(rfq, CATALOG); qid = uuid.uuid4().hex[:10]; q["id"] = qid
    QUOTES[qid] = q; return q

@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)):
    q = _process(file.filename or "upload", await file.read())
    return tpl.TemplateResponse(request, "result.html", {"q": q, "reply_text": email_reply(q) if q["source_format"] == "email" else
                                                          edi_843(q) if q["source_format"] == "edi" else ""})

@app.post("/api/quote")
async def api_quote(file: UploadFile = File(...)):
    return _process(file.filename or "upload", await file.read())

def _get(qid):
    if qid not in QUOTES: raise HTTPException(404, "Quote not found (it vanished like a ghost)")
    return QUOTES[qid]

@app.get("/quote/{qid}/pdf")
def pdf(qid: str):
    q = _get(qid)
    return Response(quotation_pdf(q), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{q["quote_no"]}.pdf"'})

@app.get("/quote/{qid}/reply")
def reply(qid: str):
    q = _get(qid); f = q["source_format"]
    if f == "fax":
        return Response(fax_cover_pdf(q), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{q["quote_no"]}-fax.pdf"'})
    if f == "edi":
        return Response(edi_843(q), media_type="text/plain", headers={"Content-Disposition": f'attachment; filename="{q["quote_no"]}.843.edi"'})
    return Response(email_reply(q), media_type="text/plain", headers={"Content-Disposition": f'attachment; filename="{q["quote_no"]}-email.txt"'})

@app.get("/health")
def health(): return {"status": "haunting", "catalog": len(CATALOG)}
