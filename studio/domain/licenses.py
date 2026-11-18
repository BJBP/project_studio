# License table of a project and what it means for selling it. license_rows(project, catalog) -> rows;
# license_alerts(rows) -> issues; license_level(rows) -> "ok" | "warn" | "error".
COPYLEFT_SOURCE = ("GPL-2.0", "GPL-3.0")


def license_rows(project: dict, catalog: dict) -> list:
    rows = []
    for slot, choice in project["slots"].items():
        component = catalog.get(choice["component"])
        if not component or component["kind"] != "software":
            continue
        lic = component["license"]
        rows.append({"slot": slot, "component": component["id"], "name": component["name"], "spdx": lic["spdx"],
                     "commercial": lic["commercial"], "notes": lic.get("notes", ""), "docs": component.get("docs", "")})
    return rows


def license_alerts(rows: list) -> list:
    alerts = []
    for row in rows:
        if row["commercial"] == "no":
            alerts.append({"code": "E_LICENSE_NONCOMMERCIAL", "component": row["name"], "spdx": row["spdx"]})
        elif "AGPL" in row["spdx"]:
            alerts.append({"code": "W_LICENSE_AGPL", "component": row["name"], "spdx": row["spdx"]})
        elif any(row["spdx"].startswith(s) for s in COPYLEFT_SOURCE):
            alerts.append({"code": "W_LICENSE_SOURCE", "component": row["name"], "spdx": row["spdx"]})
    return alerts


def license_level(rows: list) -> str:
    codes = {a["code"] for a in license_alerts(rows)}
    if "E_LICENSE_NONCOMMERCIAL" in codes:
        return "error"
    return "warn" if "W_LICENSE_AGPL" in codes else "ok"
