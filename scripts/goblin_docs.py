#!/usr/bin/env python3
"""
Goblin Docs - Minimal doc system for solo developers

Commands:
  new      Create doc from template
  check    Validate single file
  scan     Scan entire repo
  fix      Auto-fix common issues
"""

import os
import sys
import datetime
import click
import frontmatter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "doc_template.md"


@click.group()
def cli():
    """Goblin Docs - Keep chaos at bay."""
    pass


@cli.command()
@click.argument("title")
@click.option("--type", default="architecture", help="Doc type")
@click.option("--owner", default="you", help="Your name/alias")
def new(title, type, owner):
    """Create a new document."""
    if not TEMPLATE.exists():
        click.echo("❌ Template missing. Run setup first.", err=True)
        sys.exit(1)

    # Generate filename
    safe_name = re.sub(r"[^\w\-]", "_", title.lower()).strip("_")
    filename = f"{datetime.datetime.now().strftime('%Y%m%d')}_{safe_name}.md"

    # Prepare content
    content = TEMPLATE.read_text()
    replacements = {
        "{{title}}": title,
        "{{type}}": type,
        "{{owner}}": owner,
        "{{date}}": datetime.datetime.now().strftime("%Y-%m-%d"),
        "{{tag1}}": type,
        "{{tag2}}": owner,
    }

    for key, val in replacements.items():
        content = content.replace(key, val)

    # Save
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    output = docs_dir / filename

    if output.exists():
        click.confirm(f"📄 {filename} exists. Overwrite?", abort=True)

    output.write_text(content)
    click.echo(f"✅ Created: {output}")
    click.echo(f"   Preview: cat {output} | head -20")


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
def check(filepath):
    """Validate a single document."""
    try:
        post = frontmatter.load(filepath)
        required = ["title", "type", "owner", "status", "version", "last_updated"]

        missing = [r for r in required if r not in post.metadata]
        if missing:
            click.echo(f"❌ Missing: {', '.join(missing)}")
            sys.exit(1)

        click.echo("✅ Valid frontmatter")
        click.echo(f"   Title: {post.metadata['title']}")
        click.echo(f"   Status: {post.metadata['status']}")

    except Exception as e:
        click.echo(f"❌ Parse error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--path", default="docs", help="Path to scan")
def scan(path):
    """Scan all docs for issues."""
    issues = []
    for md_file in Path(path).rglob("*.md"):
        try:
            frontmatter.load(md_file)
        except Exception as e:
            issues.append(f"{md_file}: {e}")

    if issues:
        click.echo("❌ Found issues:")
        for issue in issues:
            click.echo(f"  - {issue}")
        sys.exit(1)
    click.echo("✅ All docs valid")


@cli.command()
def init():
    """Initialize the docs system."""
    click.echo("🔧 Setting up Goblin Docs...")
    # Verify structure
    (ROOT / "templates").mkdir(exist_ok=True)
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "archive").mkdir(exist_ok=True)

    click.echo("✅ Ready. Use:")
    click.echo("   python scripts/goblin_docs.py new 'My Document Title'")
    click.echo("   python scripts/goblin_docs.py check docs/my_doc.md")


if __name__ == "__main__":
    cli()
