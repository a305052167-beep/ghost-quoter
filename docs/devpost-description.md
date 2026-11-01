# Ghost Quoter · 幽灵报价员 — Fax-to-Quote

## Inspiration
I work at a Guangzhou furniture-hardware exporter. In 2026 our inbox is still haunted: buyers fax hand-annotated RFQs, paste tables into plain-text emails, or fire X12 840s from 1990s EDI systems. Every RFQ is retyped into a spreadsheet, matched to SKUs by memory, and quoted hours later. Instead of forcing buyers onto yet another portal, we decided to **resurrect** their legacy channels and make them fast.

## What it does
Upload a fax (PDF/image), an email or an EDI 840. Ghost Quoter OCRs it, extracts line items with an LLM (or an offline rule engine), matches each to our catalog with a confidence score and MOQ check, and generates a branded English quotation PDF. Then it answers **in the same language the buyer speaks**: a fax cover + quote, a plain-text email, or an EDI 843 Response to RFQ. Unknown items are flagged for a human — it never invents prices.

## How we built it
Python + FastAPI + ReportLab + pypdf. With Kiro we wrote steering docs first (product rules, tech constraints, structure), then spec'd three features in EARS format — ingestion, catalog matching, quote generation — and let Kiro execute the task lists. The UI and sample generators were vibe-coded. Agent hooks re-run tests on save and regenerate catalog docs when the CSV changes.

## Challenges we ran into
- X12 is unforgiving: separators defined by byte position, qualifier pairs, segment counts.
- Fuzzy matching "18\" BB runners" to "45mm Ball Bearing Drawer Slide 18in" without false positives (a pumpkin door knocker once matched a glass-door hinge!).
- Keeping the demo fully offline: no API key, no Tesseract.

## Accomplishments that we're proud of
- One upload → professional quote in seconds, in four formats.
- Deterministic fallback means the tool works in a factory with flaky internet.
- Specs made the EDI work correct on the first pass.

## What we learned
Spec-driven development shines for protocols; vibe coding shines for look-and-feel. Steering files are the cheapest way to stop an AI from "helpfully" inventing prices.

## What's next
Real fax in/out via eFax API, AS2 for EDI, Amazon Textract for handwriting, per-buyer price tiers, and ERP sync.

## Built with
python, fastapi, reportlab, pypdf, pillow, tesseract, openai-compatible-llm, x12-edi, kiro
