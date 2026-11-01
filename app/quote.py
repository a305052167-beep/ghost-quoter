"""Quote building + output renderers (quotation PDF, fax cover PDF, email text, EDI 843)."""
import io
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from .catalog import match

COMPANY = "Topcent Hardware (EXAMPLE) - Guangzhou, China"
ORANGE = colors.HexColor("#ff7518"); PURPLE = colors.HexColor("#2d1b4e")

@dataclass
class QuoteLine:
    line: int; requested: str; quantity: int; unit: str; sku: str; product: str
    unit_price: float; moq: int; amount: float; confidence: float; note: str; buyer_ref: str = ""

def build_quote(rfq, catalog):
    lines = []
    for i, it in enumerate(rfq.items, 1):
        p, conf = match(it.description or it.sku_hint, catalog, it.sku_hint)
        if p:
            note = "" if it.quantity >= p.moq else f"Below MOQ {p.moq}"
            lines.append(QuoteLine(i, it.description, it.quantity, p.unit, p.sku, p.name, p.unit_price_usd,
                                   p.moq, round(p.unit_price_usd * it.quantity, 2), conf, note, it.buyer_ref))
        else:
            lines.append(QuoteLine(i, it.description, it.quantity, it.unit, "", "NO MATCH - manual review",
                                   0.0, 0, 0.0, conf, "Needs human review", it.buyer_ref))
    qno = "GQ-" + datetime.now().strftime("%Y%m%d%H%M%S")
    return {"quote_no": qno, "date": date.today().isoformat(),
            "valid_until": (date.today() + timedelta(days=30)).isoformat(),
            "buyer": rfq.buyer, "reference": rfq.reference, "source_format": rfq.source_format,
            "engine": rfq.engine, "lines": [asdict(l) for l in lines],
            "total": round(sum(l.amount for l in lines), 2), "terms": "FOB Guangzhou, USD, T/T 30% deposit",
            "edi_meta": rfq.edi_meta}

def _doc(story_fn):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    doc.build(story_fn(getSampleStyleSheet())); return buf.getvalue()

def quotation_pdf(q):
    def story(ss):
        h = ss["Title"].clone("h", textColor=PURPLE)
        rows = [["#", "SKU", "Product", "Qty", "Unit", "USD/Unit", "Amount", "Note"]]
        for l in q["lines"]:
            rows.append([l["line"], l["sku"] or "-", Paragraph(l["product"], ss["BodyText"]), l["quantity"],
                         l["unit"], f'{l["unit_price"]:.3f}', f'{l["amount"]:,.2f}', l["note"]])
        rows.append(["", "", "TOTAL", "", "", "", f'{q["total"]:,.2f}', ""])
        t = Table(rows, colWidths=[20, 70, 170, 45, 35, 50, 60, 70])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PURPLE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8),
                               ("BACKGROUND", (0, -1), (-1, -1), ORANGE)]))
        return [Paragraph("QUOTATION", h), Paragraph(COMPANY, ss["Heading3"]),
                Paragraph(f'Quote No: {q["quote_no"]} &nbsp; Date: {q["date"]} &nbsp; Valid until: {q["valid_until"]}', ss["Normal"]),
                Paragraph(f'To: {q["buyer"]} &nbsp; Your ref: {q["reference"] or "-"}', ss["Normal"]), Spacer(1, 12), t,
                Spacer(1, 12), Paragraph(f'Terms: {q["terms"]}. Prices are EXAMPLE data for demo purposes.', ss["Italic"])]
    return _doc(story)

def fax_cover_pdf(q):
    def story(ss):
        big = ss["Title"].clone("big", fontSize=40, leading=48)
        return [Paragraph("FAX", big), Spacer(1, 20),
                Table([["TO:", q["buyer"]], ["FROM:", COMPANY], ["RE:", f'Quotation {q["quote_no"]} for RFQ {q["reference"] or "-"}'],
                       ["DATE:", q["date"]], ["PAGES:", "2 (incl. cover)"]], colWidths=[80, 400],
                      style=[("FONTSIZE", (0, 0), (-1, -1), 12), ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black)]),
                Spacer(1, 30), Paragraph(f'Thank you for your enquiry. {len(q["lines"])} line(s) quoted, total USD {q["total"]:,.2f}. '
                                         "Please see attached quotation. Kindly fax back signed PO to confirm.", ss["BodyText"])]
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter()
    for b in (_doc(story), quotation_pdf(q)):
        for p in PdfReader(io.BytesIO(b)).pages: w.add_page(p)
    out = io.BytesIO(); w.write(out); return out.getvalue()

def email_reply(q):
    lines = [f"Subject: Quotation {q['quote_no']} - RE: RFQ {q['reference'] or ''}".rstrip(), "",
             f"Dear {q['buyer']},", "", "Thank you for your inquiry. Please find our quotation below:", ""]
    for l in q["lines"]:
        lines.append(f"{l['line']}. {l['sku'] or '(manual review)'} {l['product']} - {l['quantity']} {l['unit']} "
                     f"x USD {l['unit_price']:.3f} = USD {l['amount']:,.2f}" + (f"  [{l['note']}]" if l["note"] else ""))
    lines += ["", f"TOTAL: USD {q['total']:,.2f}", f"Terms: {q['terms']}", f"Valid until: {q['valid_until']}", "",
              "Best regards,", "Sales Team", COMPANY]
    return "\n".join(lines)

def edi_843(q):
    m = q.get("edi_meta") or {}
    snd, rcv = m.get("receiver", "TOPCENT"), m.get("sender", "BUYER")
    now = datetime.now(); ctl = now.strftime("%H%M%S").rjust(9, "0")
    segs = [f"ISA*00*          *00*          *ZZ*{snd:<15}*ZZ*{rcv:<15}*{now:%y%m%d}*{now:%H%M}*U*00401*{ctl}*0*P*>",
            f"GS*RR*{snd.strip()}*{rcv.strip()}*{now:%Y%m%d}*{now:%H%M}*1*X*004010", "ST*843*0001",
            f"BQR*00*{q['quote_no']}*{now:%Y%m%d}*{q['reference']}", f"N1*SE*{COMPANY}", f"N1*BY*{q['buyer']}"]
    for l in q["lines"]:
        u = {"pcs": "EA", "pair": "PR", "set": "ST"}.get(l["unit"], "EA")
        segs.append(f"PO1*{l['line']}*{l['quantity']}*{u}*{l['unit_price']:.3f}**BP*{l['buyer_ref'] or l['line']}*VP*{l['sku'] or 'NOMATCH'}")
        segs.append(f"PID*F****{l['product']}")
    segs.append(f"CTT*{len(q['lines'])}")
    n = len(segs) - 2 + 1
    segs += [f"SE*{n}*0001", "GE*1*1", f"IEA*1*{ctl}"]
    return "~\n".join(segs) + "~\n"
