# Writes the delivery documents: licencias.md, THIRD_PARTY_NOTICES.md, compras.csv, and the purchase list for
# InvenTree (parts) and Odoo (products) CSV imports. Column names follow each program's import template.
# DocRenderer(t) where t(key, **params) gives the texts of the current language.
import csv
import io

COMMERCIAL_KEYS = {"yes": "doc.commercialYes", "conditions": "doc.commercialConditions", "no": "doc.commercialNo"}


class DocRenderer:
    def __init__(self, t):
        self.t = t

    def licenses_md(self, project: dict, rows: list, alerts: list) -> str:
        t = self.t
        lines = [f"# {t('doc.licensesTitle', project=project['name'])}", "", t("doc.licensesIntro"), "",
                 f"| {t('doc.colPiece')} | {t('doc.colLicense')} | {t('doc.colCommercial')} | {t('doc.colNotes')} |",
                 "|---|---|---|---|"]
        for row in rows:
            lines.append(f"| {row['name']} | {row['spdx']} | {t(COMMERCIAL_KEYS[row['commercial']])} | {row['notes']} |")
        if alerts:
            lines += ["", f"## {t('doc.alerts')}", ""] + [f"- {t('issue.' + a['code'], **a)}" for a in alerts]
        return "\n".join(lines) + "\n"

    def notices_md(self, project: dict, rows: list) -> str:
        t = self.t
        lines = [f"# THIRD_PARTY_NOTICES — {project['name']}", "", t("doc.noticesIntro"), ""]
        for row in rows:
            lines += [f"## {row['name']}", "", f"- {t('doc.colLicense')}: {row['spdx']}",
                      f"- {t('doc.source')}: {row['docs'] or '—'}", ""]
        return "\n".join(lines)

    @staticmethod
    def _csv(header: list, rows: list) -> str:
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(header)
        writer.writerows(rows)
        return out.getvalue()

    def inventree_csv(self, project: dict, shopping: dict) -> str:
        rows = [[row["name"], row["spec"], row["part"], project["name"], row["qty"]] for row in shopping["rows"]]
        return self._csv(["name", "description", "IPN", "keywords", "quantity"], rows)

    def odoo_csv(self, project: dict, shopping: dict) -> str:
        rows = []
        for row in shopping["rows"]:
            model, offer = row["model"] or {}, row["offer"] or {}
            name = f"{model.get('brand', '')} {model.get('model', '')}".strip() or row["name"]
            rows.append([name, row["part"], "consu", offer.get("price", ""), row["spec"]])
        return self._csv(["name", "default_code", "type", "standard_price", "description_purchase"], rows)

    def shopping_csv(self, shopping: dict) -> str:
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow([self.t(k) for k in ("doc.colPiece", "doc.colModel", "doc.colQty", "doc.colStore",
                                              "doc.colPrice", "doc.colCurrency", "doc.colBought")])
        for row in shopping["rows"]:
            model, offer = row["model"] or {}, row["offer"] or {}
            name = f"{model.get('brand', '')} {model.get('model', '')}".strip() or self.t("doc.toChoose")
            writer.writerow([row["name"], name, row["qty"], offer.get("store", ""), offer.get("price", ""),
                             offer.get("currency", ""), "x" if row["bought"] else ""])
        return out.getvalue()
