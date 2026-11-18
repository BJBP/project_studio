# Shopping list for N installations. Receives the project, the catalog (generic specs), the local models
# ({"models": [...]}, brands and offers from the data folder), units and the set of bought parts.
# shopping_list(...) -> {"rows": [...], "totals": {currency: amount}, "missing_prices": n, "bought": n, "issues": [...]}


def pick_model(part: str, models: list, chosen: dict) -> dict | None:
    options = [m for m in models if m["part"] == part]
    by_choice = next((m for m in options if m["id"] == chosen.get(part)), None)
    return by_choice or next((m for m in options if m.get("status") == "tested"), None) or (options[0] if options else None)


def cheapest_offer(model: dict | None) -> dict | None:
    priced = [o for o in (model or {}).get("offers", []) if o.get("price") is not None]
    return min(priced, key=lambda o: o["price"]) if priced else None


def shopping_list(project: dict, catalog: dict, models: list, units: int, bought: set, chosen: dict | None = None) -> dict:
    rows, totals, missing, issues = [], {}, 0, []
    for item in project["hardware"]:
        part = catalog.get(item["part"], {"id": item["part"], "name": item["part"], "spec": ""})
        model = pick_model(item["part"], models, chosen or {})
        offer = cheapest_offer(model)
        qty = item["qty"] * units
        if offer:
            totals[offer["currency"]] = round(totals.get(offer["currency"], 0) + offer["price"] * qty, 2)
        else:
            missing += 1
        if model and model.get("meets") is False:
            issues.append({"code": "W_MODEL_SPEC", "component": part["name"], "model": model["model"]})
        rows.append({"part": item["part"], "name": part["name"], "spec": part.get("spec", ""), "qty": qty,
                     "model": model, "options": [m for m in models if m["part"] == item["part"]],
                     "offer": offer, "bought": item["part"] in bought})
    return {"rows": rows, "totals": totals, "missing_prices": missing,
            "bought": sum(1 for r in rows if r["bought"]), "issues": issues}
