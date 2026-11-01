# Design: Quote Generation
- `build_quote(rfq, catalog) -> dict` (JSON-serialisable, stored in memory by id).
- Renderers are pure functions: `quotation_pdf`, `fax_cover_pdf` (ReportLab + pypdf merge), `email_reply`, `edi_843`.
- EDI 843: ISA/GS/ST/BQR/N1/PO1/PID/CTT/SE/GE/IEA; units pcs→EA, pair→PR, set→ST; unmatched → `VP*NOMATCH`.
- Routes: `GET /quote/{id}/pdf`, `GET /quote/{id}/reply`.
