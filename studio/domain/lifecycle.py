# The install flow: Comprar → Armar → Probar → Instalar → Entregar → Soporte, each with its checklist.
# stages_view(project, catalog, done) -> {"stages": [...], "done": n, "total": n}. "Comprar" is built from the
# hardware list; item ids are "<stage>.<item>" so one set of done ids covers the whole project.


def stage_items(stage: dict, project: dict, catalog: dict) -> list:
    if stage.get("source") == "hardware":
        return [{"id": item["part"], "text": f"{catalog.get(item['part'], {}).get('name', item['part'])} ×{item['qty']}"}
                for item in project["hardware"]]
    return stage.get("items", [])


def stages_view(project: dict, catalog: dict, done: set) -> dict:
    stages, total, finished = [], 0, 0
    for stage in project["stages"]:
        items = []
        for item in stage_items(stage, project, catalog):
            item_id = f"{stage['id']}.{item['id']}"
            items.append({**item, "id": item_id, "done": item_id in done})
        stage_done = sum(1 for i in items if i["done"])
        stages.append({"id": stage["id"], "name": stage["name"], "items": items,
                       "done": stage_done, "total": len(items)})
        total += len(items)
        finished += stage_done
    return {"stages": stages, "done": finished, "total": total}


def item_exists(project: dict, catalog: dict, item_id: str) -> bool:
    return any(item_id == item["id"] for stage in stages_view(project, catalog, set())["stages"]
               for item in stage["items"])
