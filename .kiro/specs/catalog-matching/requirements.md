# Requirements: Catalog Matching
1. THE SYSTEM SHALL load products from `data/catalog.csv` (sku, name, category, keywords, unit, moq, unit_price_usd, finish).
2. WHEN a line item carries a `sku_hint` equal to a catalog SKU, THE SYSTEM SHALL match it with confidence 1.0.
3. WHEN no SKU hint matches, THE SYSTEM SHALL score products by token overlap with synonym and size normalisation (e.g. `18"` → `18 inch`).
4. IF the requested text contains sizes not present in a product, THEN THE SYSTEM SHALL penalise that product's score.
5. IF the best score is below 0.45, THEN THE SYSTEM SHALL return no match and the line SHALL be flagged for manual review.
6. WHEN quantity is below the product MOQ, THE SYSTEM SHALL add a "Below MOQ" note.
