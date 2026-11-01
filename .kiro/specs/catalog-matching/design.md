# Design: Catalog Matching
- `tokens()` lowercases, splits `18mm` into `18mm 18 mm`, maps synonyms (runners→slide, pulls→pull).
- score = |query ∩ product| / |query| × (0.5 if query numbers ∉ product else 1).
- Threshold 0.45 tuned so "pumpkin door knocker" does not match "glass door hinge".
- Future: embedding search via MCP vector store; per-buyer price lists.
