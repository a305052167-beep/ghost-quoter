"""Catalog loading + fuzzy matching. EXAMPLE DATA ONLY - not real Topcent prices."""
import csv, re
from dataclasses import dataclass
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "catalog.csv"
TOKEN = re.compile(r"[a-z0-9]+")
SYNONYMS = {"hinges": "hinge", "slides": "slide", "runners": "slide", "runner": "slide", "pulls": "pull",
            "handles": "handle", "knobs": "knob", "softclose": "soft close", "sc": "soft close",
            "inches": "inch", "in": "inch", '"': "inch", "undermount": "undermount", "struts": "strut"}

@dataclass
class Product:
    sku: str; name: str; category: str; keywords: str; unit: str; moq: int; unit_price_usd: float; finish: str

def load_catalog(path=CATALOG_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return [Product(r["sku"], r["name"], r["category"], r["keywords"], r["unit"], int(r["moq"]),
                        float(r["unit_price_usd"]), r["finish"]) for r in csv.DictReader(f)]

def tokens(text):
    text = text.lower().replace('"', " inch ").replace("-", " ")
    text = re.sub(r"(\d+)\s*(mm|in|inch|n)\b", r"\1\2 \1 \2", text)
    out = []
    for t in TOKEN.findall(text):
        out.extend(SYNONYMS.get(t, t).split())
    return set(out)

def match(description, catalog, sku_hint=None):
    """Return (product, confidence 0..1) or (None, 0)."""
    if sku_hint:
        for p in catalog:
            if p.sku.lower() == sku_hint.lower():
                return p, 1.0
    q = tokens(description)
    if not q:
        return None, 0.0
    best, best_score = None, 0.0
    for p in catalog:
        ptoks = tokens(p.name + " " + p.keywords + " " + p.category)
        hit = q & ptoks
        nums_q = {t for t in q if any(c.isdigit() for c in t)}
        num_penalty = 0.5 if nums_q and not (nums_q & ptoks) else 1.0
        score = (len(hit) / len(q)) * num_penalty
        if score > best_score:
            best, best_score = p, score
    return (best, round(best_score, 2)) if best_score >= 0.45 else (None, round(best_score, 2))
