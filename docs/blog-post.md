# Resurrecting the Fax Machine: Building Ghost Quoter with Kiro

*This post was written for the Kiroween 2026 hackathon (#KiroweenHackathon26).*

At a hardware export company in Guangzhou, the scariest thing on Halloween isn't a ghost — it's the fax machine whirring at 3 a.m. with another RFQ for 5,000 soft-close hinges. Our buyers range from modern e-commerce brands to 40-year-old cabinet makers who trust fax and EDI more than any web portal.

So for Kiroween's **Resurrection** category, I built **Ghost Quoter (幽灵报价员)**: it reads RFQs from fax, email or EDI X12 840, extracts line items, matches them to our catalog, and replies in the same format — fax PDF, email text, or EDI 843.

## Steering first
Before any code, I wrote three Kiro steering files. The most important rule: *never invent a price*. Every time Kiro generated matching code, unmatched items got flagged for manual review instead of a guessed SKU.

## Specs for the hard parts
EDI parsing and fuzzy matching went through Kiro specs: EARS requirements ("IF the best score is below 0.45, THEN THE SYSTEM SHALL return no match"), a design doc and a task list. Kiro worked through the tasks one by one, and tests kept it honest.

## Vibe coding for the fun parts
The purple-and-pumpkin UI with a floating ghost? Pure vibe coding — "make it spooky but keep the PDFs boring" was enough.

## Hooks
A save hook runs pytest; a catalog hook regenerates the catalog docs whenever the CSV changes.

## Result
A runnable FastAPI app that works fully offline with a rule-based extractor, and gets smarter with any OpenAI-compatible LLM. Old tech isn't dead — it just needed a ghost to answer it.
