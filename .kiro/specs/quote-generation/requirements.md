# Requirements: Quote Generation & Format-Matched Replies
1. THE SYSTEM SHALL produce a quote with number, date, 30-day validity, buyer, reference, lines, total and FOB terms.
2. WHEN the user requests the quotation, THE SYSTEM SHALL return a branded English PDF.
3. WHEN the source was a fax, THE SYSTEM SHALL return a fax cover page merged with the quotation PDF.
4. WHEN the source was email, THE SYSTEM SHALL return a plain-text email reply.
5. WHEN the source was EDI 840, THE SYSTEM SHALL return an X12 843 Response to RFQ echoing the buyer reference and ISA partners swapped.
6. IF a quote id is unknown, THEN THE SYSTEM SHALL return HTTP 404.
