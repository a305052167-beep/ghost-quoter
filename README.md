# 👻 Ghost Quoter · 幽灵报价员 — Fax-to-Quote

> Kiroween 2026 · Category: **Resurrection** — reviving fax, plain-text email and EDI X12 840 to solve today's quoting bottleneck.

Overseas buyers of furniture hardware (hinges, drawer slides, handles…) still send RFQs by **fax**, **plain-text email** or **legacy EDI**. Ghost Quoter ingests them, extracts line items (LLM or offline rules), matches them to the product catalog, and produces a branded English quotation PDF — then **replies in the buyer's original format**: fax cover + quote PDF, text email, or **EDI 843**.

> ⚠️ `data/catalog.csv` contains ~30 **example** SKUs and prices. Buyers in samples are fictional.

## Features
- Upload page → results table with match confidence, MOQ warnings, "manual review" for unknown items (never invents prices)
- Ingest: fax PDF (text layer) / image (Tesseract OCR if installed), email `.txt/.eml`, EDI X12 840
- Pluggable LLM extraction (any OpenAI-compatible API) with deterministic rule-based fallback — demo works with no key
- Outputs: quotation PDF, fax-style reply PDF, email reply text, X12 843 Response to RFQ
- JSON API: `POST /api/quote`
- Spooky-but-professional UI (the documents stay professional)

## Run
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload        # open http://127.0.0.1:8000
pytest -q                            # tests
python scripts/make_samples.py       # regenerate fake fax samples
```
Upload anything in `samples/` (`rfq_email.txt`, `rfq_840.edi`, `rfq_fax.pdf`, `rfq_fax.png`).

Optional LLM:
```bash
export GHOST_LLM_API_KEY=sk-...  GHOST_LLM_BASE_URL=https://api.openai.com/v1  GHOST_LLM_MODEL=gpt-4o-mini
```
Optional OCR: `apt install tesseract-ocr && pip install pytesseract`. Docker: `docker build -t ghost-quoter . && docker run -p 8000:8000 ghost-quoter`.

## Architecture
```
 fax PDF/PNG ─┐                       ┌─ LLM (OpenAI-compatible) ─┐
 email .txt ──┼─ detect_format ─ OCR ─┤                           ├─ RFQ ─ catalog match ─ Quote ─┬─ quotation PDF
 EDI 840 ─────┘   └─ X12 840 parser ──┴─ rules fallback ──────────┘        (data/catalog.csv)     ├─ fax reply PDF
                                                                                                  ├─ email reply
                                                                                                  └─ EDI 843
```
| File | Role |
|---|---|
| `app/extract.py` | format detection, OCR chain, EDI 840 parser, LLM + rules extractors |
| `app/catalog.py` | CSV catalog + token/synonym/size matcher |
| `app/quote.py` | quote builder + PDF/fax/email/EDI 843 renderers |
| `app/main.py` | FastAPI routes & templates |

## How we used Kiro
- **Steering** (`.kiro/steering/`): `product.md` (never invent prices, professional docs), `tech.md` (offline fallback is mandatory, minimal deps), `structure.md` (where new formats go). These kept every generated change consistent.
- **Specs vs vibe coding**: the three core features — `multi-format-ingestion`, `catalog-matching`, `quote-generation` — were built spec-first (EARS requirements → design → tasks) because EDI segments and matching thresholds need precision. The Halloween UI, CSS ghost animation and sample generators were vibe-coded in chat — fast iteration where exactness didn't matter.
- **Hooks** (`.kiro/hooks/`): `run-tests-on-save` runs pytest when app/tests change; `update-catalog-docs` regenerates `docs/catalog.md` and re-checks the matcher when the catalog CSV changes.
- **MCP** (`.kiro/settings/mcp.json.example`): fetch server for X12 reference lookups, AWS docs server (for a future Textract OCR backend), filesystem server scoped to `samples/` and `data/`. Copy to `.kiro/settings/mcp.json` to enable.

## Limitations
- Rules extractor handles common "description – qty unit" layouts; messy faxes benefit from the LLM.
- Without Tesseract, PNG faxes only work if they carry the embedded `ghost-ocr` text (the demo sample does); PDF faxes with a text layer always work.
- Quotes are in-memory (lost on restart). EDI 843 is a simplified 4010 subset, not validated against a trading partner's implementation guide.
- No fax/AS2 transmission — reply files are downloaded.

## License
MIT
