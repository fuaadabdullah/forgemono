#!/usr/bin/env python3
"""
goblin_docs.py — simple doc templater + validator CLI
"""

import sys
import datetime
import click
import frontmatter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"
TEMPL = TEMPLATES_DIR / "doc_template.md"

REQUIRED_FRONTMATTER = ["title", "type", "owner", "status", "version", "last_updated"]


def render_template(values: dict) -> str:
    txt = TEMPL.read_text()
    for k, v in values.items():
        txt = txt.replace("{{" + k + "}}", v)
    return txt


@click.group()
def cli():
    pass


@cli.command()
@click.argument("name")
@click.option("--type", default="other")
@click.option("--owner", default="fuaad")
@click.option("--dir", default="docs")
def new(name, type, owner, dir):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    safe_title = re.sub(r"[^\w\- ]", "", name).strip().replace(" ", "_").upper()
    filename = f"{safe_title}.md"
    outdir = Path(dir)
    outdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "title": name,
        "type": type,
        "owner": owner,
        "date": now,
        "tag1": type,
        "tag2": owner,
    }
    content = render_template(payload)
    fpath = outdir / filename
    if fpath.exists():
        click.confirm(f"{fpath} exists. Overwrite?", abort=True)
    fpath.write_text(content)
    click.echo(f"Created {fpath}")


@cli.command()
@click.option("--path", default=".")
def validate(path):
    path = Path(path)
    md_files = list(path.rglob("*.md"))
    errors = []
    for md in md_files:
        try:
            post = frontmatter.load(md)
        except Exception as e:
            errors.append(f"BAD FRONTMATTER: {md} : {e}")
            continue
        for k in REQUIRED_FRONTMATTER:
            if k not in post.metadata:
                errors.append(f"MISSING {k} in {md}")
        # quick sanity checks
        if "version" in post.metadata:
            if not re.match(r"^\d+\.\d+\.\d+$", str(post.metadata["version"])):
                errors.append(f"BAD VERSION in {md} : {post.metadata.get('version')}")
    if errors:
        click.echo("Validation FAILED:")
        for e in errors:
            click.echo(" - " + e)
        sys.exit(2)
    click.echo("Validation passed ✅")


if __name__ == "__main__":
    cli()
