---
inclusion: always
---
# Structure
- `app/extract.py` ingestion: format detection, OCR, EDI 840 parser, rules + LLM extractors → `RFQ`/`LineItem`.
- `app/catalog.py` catalog CSV load + token-overlap matcher.
- `app/quote.py` quote building + renderers (quotation PDF, fax cover PDF, email text, EDI 843).
- `app/main.py` FastAPI routes; `app/templates`, `app/static` UI.
- `data/` catalog, `samples/` demo RFQs (`scripts/make_samples.py` regenerates fax samples), `tests/` pytest.
- New output formats go in `quote.py` as pure functions `(quote_dict) -> bytes|str`.
