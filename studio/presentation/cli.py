# Command line for people and agents. Exit 0 = OK; otherwise one "<CODE>: <message>" line per problem.
#   uv run --no-project python -m studio list   <data>
#   uv run --no-project python -m studio check  <data> <project>
#   uv run --no-project python -m studio export <data> <project> <output folder>
import argparse
import sys
from pathlib import Path

from studio.application import shopping as shop
from studio.application import use_cases as uc
from studio.infrastructure.render import DocRenderer
from studio.presentation.messages import describe, t
from studio.presentation.wiring import build_repo


def run(args) -> int:
    repo = build_repo(args.data)
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
    parser.add_argument("command", choices=["list", "check", "export"])
    parser.add_argument("data", help=t("cli.dataHelp"))
    parser.add_argument("project", nargs="?")
    parser.add_argument("output", nargs="?", default="entrega")
    args = parser.parse_args(argv)
    if args.command != "list" and not args.project:
        parser.error(t("cli.needProject"))
    try:
        return run(args)
    except uc.StudioError as err:
        issue = describe({"code": err.code, **err.params})
        print(f"{issue['code']}: {issue['message']}")
        return 2
