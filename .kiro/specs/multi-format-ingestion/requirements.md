# Requirements: Multi-format RFQ Ingestion
## User story
As an export sales rep, I want to upload any RFQ (fax, email, EDI 840) so that line items are extracted without re-typing.

## Acceptance criteria (EARS)
1. WHEN a file starting with `ISA` or ending `.edi/.x12/.840` is uploaded, THE SYSTEM SHALL parse it as X12 840 and extract BQT reference, N1*BY buyer, and PO1/PID line items.
2. WHEN a PDF or image is uploaded, THE SYSTEM SHALL treat it as a fax and obtain text via PDF text layer, else OCR.
3. WHEN any other file is uploaded, THE SYSTEM SHALL treat it as plain-text email.
4. WHERE `GHOST_LLM_API_KEY` is set, THE SYSTEM SHALL use the OpenAI-compatible LLM to extract buyer, reference and items as JSON.
5. IF the LLM is not configured, fails, or returns invalid JSON, THEN THE SYSTEM SHALL use the rule-based extractor.
6. THE SYSTEM SHALL normalise units to `pcs`, `pair` or `set`.
7. IF the uploaded file is empty, THEN THE SYSTEM SHALL respond with HTTP 400.
