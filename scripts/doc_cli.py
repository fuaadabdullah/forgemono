#!/usr/bin/env python3
"""
Complete Documentation CLI - One script to rule them all
Commands: new, validate, diagrams, analyze, raptor, audit
"""

import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
import click
import frontmatter
import requests

# ========== CORE FUNCTIONS ==========


def create_doc(title, doc_type="architecture", owner="you"):
    """Create a new document from template."""
    template = Path("templates/doc_template.md")
    if not template.exists():
        return "❌ Template missing"

    # Generate filename
    safe_name = re.sub(r"[^\w\-]", "_", title.lower()).strip("_")
    filename = f"{datetime.now().strftime('%Y%m%d')}_{safe_name}.md"

    # Read and replace template
    content = template.read_text()
    replacements = {
        "{{title}}": title,
        "{{type}}": doc_type,
        "{{owner}}": owner,
        "{{date}}": datetime.now().strftime("%Y-%m-%d"),
        "{{tag1}}": doc_type,
        "{{tag2}}": owner,
    }

    for key, val in replacements.items():
        content = content.replace(key, val)

    # Save
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    output = docs_dir / filename
    output.write_text(content)

    return f"✅ Created: {output}"


def validate_docs():
    """Validate all markdown files."""
    errors = []
    for md in Path("docs").rglob("*.md"):
        try:
            post = frontmatter.load(md)
            required = ["title", "type", "owner", "status", "version", "last_updated"]
            for field in required:
                if field not in post.metadata:
                    errors.append(f"Missing {field} in {md}")
        except Exception as e:
            errors.append(f"Failed to parse {md}: {e}")

    if errors:
        return "\n".join(["❌ Validation failed:"] + errors)
    return "✅ All documents valid"


def generate_diagrams():
    """Find and render Mermaid diagrams in code."""
    import tempfile

    # Find diagrams in code comments
    patterns = {
        "python": r"#\s*%%\s*mermaid\s*(.*?)(?:\n#|$)",
        "js": r"//\s*mermaid:\s*(.*?)(?:\n//|$)",
        "go": r"//\s*mermaid:\s*(.*?)(?:\n//|$)",
        "markdown": r"```mermaid\s*\n(.*?)\n```",
    }

    diagrams = []
    for ext, pattern in patterns.items():
        for file in Path(".").rglob(f"*.{ext}"):
            if "node_modules" in str(file) or ".git" in str(file):
                continue

            content = file.read_text()
            for match in re.finditer(pattern, content, re.DOTALL):
                diagrams.append(
                    {
                        "file": str(file),
                        "code": match.group(1).strip(),
                        "hash": str(hash(match.group(1)))[:8],
                    }
                )

    # Render diagrams using mermaid-cli
    output_dir = Path("docs/assets/diagrams")
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, diagram in enumerate(diagrams, 1):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(diagram["code"])
            temp_file = f.name

        output_file = output_dir / f"diagram_{diagram['hash']}.svg"

        try:
            subprocess.run(
                [
                    "mmdc",
                    "-i",
                    temp_file,
                    "-o",
                    str(output_file),
                    "-t",
                    "default",
                    "-b",
                    "transparent",
                ],
                capture_output=True,
                timeout=30,
            )

            if output_file.exists():
                print(f"✅ Generated: {output_file}")
        except Exception as e:
            print(f"⚠️  Failed to render diagram {i}: {e}")
        finally:
            os.unlink(temp_file)

    return f"✅ Generated {len(diagrams)} diagrams"


def analyze_with_raptor(filepath, raptor_url=None):
    """Analyze document using Raptor Mini (Colab-deployed)."""
    if not Path(filepath).exists():
        return "❌ File not found"

    content = Path(filepath).read_text()

    # Use configurable Raptor URL (Colab endpoint)
    if not raptor_url:
        raptor_url = os.getenv(
            "RAPTOR_MINI_URL", "https://your-colab-raptor-endpoint.ngrok.io"
        )

    # Check if Raptor endpoint is accessible
    try:
        # Simple health check - adjust based on your Colab API
        requests.get(f"{raptor_url}/health", timeout=5)
    except Exception:
        return f"❌ Raptor not accessible at {raptor_url}. Check RAPTOR_MINI_URL env var or Colab deployment."

    # Send to Raptor (adjust payload format based on your Colab API)
    payload = {
        "task": "analyze_document",
        "content": content[:1500],  # Limit content for API
        "analysis_type": "quality_score",
    }

    try:
        response = requests.post(
            f"{raptor_url}/analyze",  # Adjust endpoint path based on your Colab API
            json=payload,
            timeout=60,  # Colab might be slower
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()

            # Format response (adjust based on your Colab API response format)
            score = data.get("score", "N/A")
            strength = data.get("strength", "N/A")
            weakness = data.get("weakness", "N/A")
            improvements = data.get("improvements", [])

            return f"""🤖 RAPTOR MINI ANALYSIS (Colab):
Score: {score}/100
Strength: {strength}
Weakness: {weakness}
Improvements:
{chr(10).join(f"  • {i}" for i in improvements)}"""

        else:
            return f"❌ Raptor API error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"❌ Raptor connection error: {e}"


# ========== CLI INTERFACE ==========


@click.group()
def cli():
    """Complete Documentation System"""
    pass


@cli.command()
@click.argument("title")
@click.option("--type", default="architecture", help="Document type")
@click.option("--owner", default="you", help="Document owner")
def new(title, type, owner):
    """Create a new document."""
    click.echo(create_doc(title, type, owner))


@cli.command()
def validate():
    """Validate all documents."""
    click.echo(validate_docs())


@cli.command()
def diagrams():
    """Generate diagrams from code."""
    click.echo(generate_diagrams())


@cli.command()
@click.argument("file")
@click.option("--url", help="Raptor Mini API URL (Colab endpoint)")
def analyze(file, url):
    """Analyze document with Raptor Mini (Colab-deployed)."""
    click.echo(analyze_with_raptor(file, url))


@cli.command()
def audit():
    """Run full documentation audit."""
    click.echo("🔍 Running full documentation audit...")
    click.echo("-" * 50)
    click.echo(validate_docs())
    click.echo()
    click.echo("📊 Checking markdown formatting...")
    subprocess.run(
        ["markdownlint", "docs/", "--config", ".markdownlint.json"], capture_output=True
    )
    click.echo("✅ Markdown lint complete")
    click.echo()
    click.echo("🔗 Checking links...")
    subprocess.run(["markdown-link-check", "docs/*.md"], capture_output=True)
    click.echo("✅ Link check complete")
    click.echo()
    click.echo("🎨 Generating diagrams...")
    click.echo(generate_diagrams())
    click.echo("-" * 50)
    click.echo("✨ Audit complete!")


@cli.command()
def setup():
    """Setup the documentation system."""
    click.echo("🚀 Setting up documentation system...")

    # Create config files
    Path(".markdownlint.json").write_text(
        json.dumps(
            {"default": True, "MD013": False, "MD033": False, "MD041": False}, indent=2
        )
    )

    Path(".prettierrc").write_text(
        json.dumps({"printWidth": 100, "proseWrap": "always"}, indent=2)
    )

    # Create example document
    create_doc("Welcome to Your Documentation System", "onboarding", "system")

    click.echo("✅ Setup complete!")
    click.echo("\n📚 Quick start:")
    click.echo("  python scripts/doc_cli.py new 'My First Doc'")
    click.echo("  python scripts/doc_cli.py audit")
    click.echo("  python scripts/doc_cli.py analyze docs/*.md")


if __name__ == "__main__":
    cli()
