# Does the project fit on each computer, and which variant (lighter AI, lighter speech model) to use there?
# fit(project, catalog, equipment) -> {"id", "name", "ram_needed", "ram_total", "ok", "items": [...], "issues": [...]}


def choose_variant(component: dict, wanted: str | None, has_gpu: bool) -> dict | None:
    variants = component.get("variants", [])
    if not variants:
        return None
    current = next((v for v in variants if v["id"] == wanted), variants[0])
    if has_gpu:
        return current
    # Without GPU the heavy variant answers too slowly: take the first one that needs no GPU.
    return next((v for v in variants if v["needs"].get("gpu") == "none"), current)


def fit(project: dict, catalog: dict, equipment: dict) -> dict:
    has_gpu = equipment.get("gpu_vram_gb", 0) > 0
    items, issues, ram = [], [], 0.0
    for slot, choice in project["slots"].items():
        component = catalog.get(choice["component"])
        if not component or component["kind"] != "software":
            continue
        variant = choose_variant(component, choice.get("variant"), has_gpu)
        needs = (variant or {}).get("needs", component["needs"])
        ram += needs.get("ram_gb", 0)
        speed = (variant or {}).get("speed", {}).get("gpu" if has_gpu else "cpu")
        if variant and choice.get("variant") and variant["id"] != choice["variant"]:
            issues.append({"code": "W_VARIANT_SWITCH", "component": component["name"],
                           "from": choice["variant"], "to": variant["id"], "equipment": equipment["name"]})
        items.append({"slot": slot, "component": component["name"], "variant": variant and variant["label"],
                      "speed": speed, "ram_gb": needs.get("ram_gb", 0)})
    ok = ram <= equipment["ram_gb"]
    if not ok:
        issues.append({"code": "E_RAM_SHORT", "equipment": equipment["name"], "need": round(ram, 1),
                       "have": equipment["ram_gb"]})
    return {"id": equipment["id"], "name": equipment["name"], "icon": equipment.get("icon", ""),
            "role": equipment.get("role", ""), "ram_needed": round(ram, 1), "ram_total": equipment["ram_gb"],
            "gpu": has_gpu, "ok": ok, "items": items, "issues": issues}
