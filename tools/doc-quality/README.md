# Documentation Quality Checker

A CLI tool for automated documentation quality analysis using AI-powered scoring via the Raptor Mini API.

## Features

- **AI-Powered Analysis**: Uses advanced language models to evaluate documentation quality
- **Comprehensive Metrics**: Analyzes clarity, completeness, structure, accuracy, and readability
- **CI/CD Integration**: Quality gates for automated pipelines
- **Batch Processing**: Efficiently handles large numbers of files
- **Detailed Reporting**: Generate comprehensive quality reports
- **Debug Tools**: Extensive debugging and API response saving capabilities

## Quick Start

```bash
# Check all documentation files
python3 doc_quality_check.py

# Check specific files
python3 doc_quality_check.py docs/README.md docs/WORKSPACE_OVERVIEW.md

# CI mode with quality gate
python3 doc_quality_check.py --ci --min-score 70
# Dev mode - Phi only (fast local feedback)
export RAPTOR_MODE=phi_only
python3 doc_quality_check.py --path docs/ --mode phi_only

# Polish mode - dual: Phi then Raptor polish
export RAPTOR_MODE=dual
python3 doc_quality_check.py --path docs/ --mode dual --polish


# Generate detailed report
python3 doc_quality_check.py --report ../../../docs/reports/quality_report.md
```

## Developer Setup & Tests

Install dependencies for development and tests:

```bash

python3 -m pip install -r requirements.txt
python3 -m pip install -r ../raptor-mini/requirements.txt
```

Run unit tests for doc-quality and raptor-mini:

```bash
python3 -m pytest -q tools/raptor-mini/tests tools/doc-quality/tests
```
## Installation

1. Ensure Python 3.9+ is installed
1. Install dependencies:
   ```bash

   pip install requests pyyaml
   ```

1. The Raptor Mini API should be running (default: ngrok URL)

## Configuration

Customize behavior via `doc_quality_config.yaml`:

```yaml
api:
  url: "https://your-api-url.ngrok-free.dev"
  timeout: 15
  retries: 3

quality:
  min_score: 60
  high_quality_threshold: 80
  medium_quality_threshold: 60
  ci_fail_threshold: 70

files:
  directories: ["docs", "."]
  extensions: [".md", ".txt", ".rst", ".adoc"]
  exclude_patterns: ["**/node_modules/**", "**/.git/**"]
```

## Quality Metrics

The tool analyzes documentation for:

- **Clarity**: Clear, understandable content
- **Completeness**: Comprehensive coverage of topics
- **Structure**: Well-organized sections and headings
- **Accuracy**: Technically correct information
- **Readability**: Appropriate language and formatting

**Scoring Scale:**
- **High Quality**: ≥80/100
- **Medium Quality**: 60-79/100
- **Low Quality**: <60/100

## Usage Examples

### Basic Quality Check
```bash

python3 doc_quality_check.py
```

### CI Mode with Quality Gates

```bash
python3 doc_quality_check.py --ci --min-score 70
```

### Generate Reports
```bash

python3 doc_quality_check.py --report ../../../docs/reports/quality_report.md
```

### Debug Mode

```bash
python3 doc_quality_check.py --debug --debug-api --debug-timing
```

### Save API Responses
```bash

python3 doc_quality_check.py --save-responses ./debug_responses
```

## Soft fallback (phi-only)

If you want phi_only mode to attempt to fall back to the hosted Raptor API when the local Phi-3 process is unavailable, you can enable `soft_fallback`.

1. CLI usage (single-run):

```bash
python3 doc_quality_check.py --mode phi_only --soft-fallback --path docs/
```

1. Config (persist across runs):

```yaml

models:
  phi3:
    soft_fallback: true
```

1. Pre-commit usage (env var):

```bash
export DOC_QUALITY_SOFT_FALLBACK=true
```

The pre-commit script will pass `--soft-fallback` on the CLI when set.


## Integration

### Git Pre-commit Hook

```bash

cp pre-commit-doc-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### CI/CD Pipeline

Add to your CI pipeline:

```yaml
- name: Check Documentation Quality
  run: python3 tools/doc-quality/doc_quality_check.py --ci --min-score 70
```

## Files

- `doc_quality_check.py` - Main CLI tool
- `doc_quality_config.yaml` - Configuration file
- `../docs/DOC_QUALITY_AUTOMATION.md` - Detailed documentation

## Dependencies

- Python 3.9+
- requests
- pyyaml
- Raptor Mini API (running instance)

## Troubleshooting

- **API connectivity issues**: Check Raptor Mini server status
- **Quality scoring problems**: Review analysis output for suggestions
- **Configuration errors**: Validate YAML syntax in config file
- **Integration issues**: Check CI logs and pre-commit hook output</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/tools/doc-quality/README.md
