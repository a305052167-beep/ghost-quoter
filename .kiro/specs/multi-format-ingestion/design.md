# Design: Multi-format Ingestion
```
upload → detect_format ─┬─ edi  → parse_edi_840 ───────────────┐
                        ├─ fax  → ocr() → text ─┐               │
                        └─ email → decode ──────┴→ llm_extract? ─┴→ RFQ
                                                   └ rules_extract (fallback)
```
- `RFQ{source_format,buyer,reference,raw_text,items[],engine,edi_meta}`; `LineItem{description,quantity,unit,buyer_ref,sku_hint}`.
- OCR chain: pypdf text layer → pytesseract (if installed) → PNG `ghost-ocr` tEXt chunk (demo-only fallback).
- Rules: regexes for "desc - N pcs", "N pcs desc", "desc x N pairs"; skips header lines (From/To/Tel/Fax).
- EDI: segment terminator from ISA position 105, element separator `*`; PO1 qualifier pairs (BP buyer part, VP vendor part → sku_hint).
