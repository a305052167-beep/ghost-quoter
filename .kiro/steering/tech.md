---
inclusion: always
---
# Tech
- Python 3.11+, FastAPI + Jinja2 templates, ReportLab (PDF), pypdf (PDF text + merge), Pillow; pytesseract optional.
- LLM: any OpenAI-compatible endpoint via env `GHOST_LLM_API_KEY`, `GHOST_LLM_BASE_URL`, `GHOST_LLM_MODEL`. Must ALWAYS fall back to the deterministic rules extractor on missing key or any error.
- No database: catalog is `data/catalog.csv`; quotes kept in memory.
- Tests: pytest, `pytest -q` must pass offline (no network, no key, no tesseract).
- Keep dependencies minimal; stdlib `urllib` for HTTP.
