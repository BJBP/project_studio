# Command line for people and agents. Exit 0 = OK; otherwise one "<CODE>: <message>" line per problem.
#   uv run --no-project python -m studio list   <data>
#   uv run --no-project python -m studio check  <data> <project>
#   uv run --no-project python -m studio export <data> <project> <output folder>
#   uv run --no-project python -m studio modules <data> [list | enable <id> | disable <id> | install <zip> | uninstall <id>]
import argparse
import sys
from pathlib import Path

from studio.application import modules as mods
from studio.application import shopping as shop
from studio.application import use_cases as uc
from studio.infrastructure.render import DocRenderer
from studio.presentation.messages import describe, t
from studio.presentation.wiring import build_modules, build_repo


def run_modules(repo, action: str, module_id: str | None) -> int:
    store = build_modules(repo)
    if action == "install":
        try:
            data = Path(module_id or "").read_bytes()
        except OSError:
            raise uc.StudioError("E_EXT_BAD_ZIP") from None
        result = mods.install_package(store, data)
    elif action == "uninstall":
        result = mods.uninstall_module(store, module_id or "")
    else:
        result = mods.list_modules(store) if action == "list" else mods.set_enabled(store, module_id or "", action == "enable")
    for item in result["modules"]:
        print(f"{item['id']}	{item['name']}	{item['version']}	{'activo' if item['active'] else 'apagado'}")
    for issue in result["issues"]:
        print(f"{issue['code']}: {describe(issue)['message']}")
    return 1 if result["issues"] else 0


def run(args) -> int:
    repo = build_repo(args.data)
    if args.command == "modules":
        return run_modules(repo, args.project or "list", args.output if args.output != "entrega" else None)
    if args.command == "list":
        for card in uc.list_projects(repo):
            print(f"{card['id']}\t{card['name']}\t{card['status']}\t{t('cli.licenses')}: {card['licenses']}")
        return 0
    if args.command == "check":
        issues = [describe(i) for i in uc.check_project(repo, args.project)]
        errors = [i for i in issues if i["code"].startswith("E_")]
        for issue in issues:
            print(f"{issue['code']}: {issue['message']}")
        if not issues:
            print(t("cli.ok", project=args.project))
        return 1 if errors else 0
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in shop.export_docs(repo, args.project, DocRenderer(t)).items():
        (out / name).write_text(text, encoding="utf-8")
        print(out / name)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="studio", description=t("cli.description"))
    parser.add_argument("command", choices=["list", "check", "export", "modules"])
    parser.add_argument("data", help=t("cli.dataHelp"))
    parser.add_argument("project", nargs="?")
    parser.add_argument("output", nargs="?", default="entrega")
    args = parser.parse_args(argv)
    if args.command not in ("list", "modules") and not args.project:
        parser.error(t("cli.needProject"))
    try:
        return run(args)
    except uc.StudioError as err:
        issue = describe({"code": err.code, **err.params})
        print(f"{issue['code']}: {issue['message']}")
        return 2
