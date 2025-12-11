# Documentation Quality Automation

This system provides automated quality checks for ForgeMonorepo documentation using the Raptor Mini API.

## 🚀 Quick Start

### Basic Usage

```bash
# Check all documentation files
python3 tools/doc-quality/doc_quality_check.py

# Check specific files
python3 tools/doc-quality/doc_quality_check.py docs/README.md docs/WORKSPACE_OVERVIEW.md

# CI mode with quality gate
python3 tools/doc-quality/doc_quality_check.py --ci --min-score 70

# Generate detailed report
python3 tools/doc-quality/doc_quality_check.py --report docs/reports/quality_report.md
```

### Installation

1. Ensure Python 3.9+ is installed
2. Install dependencies:
   ```bash

   pip install requests pyyaml
   ```

3. The Raptor Mini API should be running (default: ngrok URL)

## 📊 Quality Metrics

The system analyzes documentation for:

- **Clarity**: Clear, understandable content
- **Completeness**: Comprehensive coverage of topics
- **Structure**: Well-organized sections and headings
- **Accuracy**: Technically correct information
- **Readability**: Appropriate language and formatting

Scores range from 0-100, with thresholds:

- **High Quality**: ≥80
- **Medium Quality**: 60-79
- **Low Quality**: <60

## 🛠️ Configuration

Customize behavior via `tools/doc-quality/doc_quality_config.yaml`:

```yaml
api:
  url: "https://your-api-url.ngrok-free.dev"
  timeout: 15

quality:
  min_score: 60
  ci_fail_threshold: 70

files:
  directories: ["docs", "."]
  extensions: [".md", ".txt", ".rst", ".adoc"]
```

## 🔧 Integration Options

### Git Pre-commit Hook

Automatically check documentation quality before commits:

```bash

# Install the hook
cp pre-commit-doc-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Now quality checks run on every commit with staged docs
```

### CI/CD Pipeline

The system includes GitHub Actions workflow (`.github/workflows/docs-ci.yml`) that:

- Runs on pushes/PRs affecting documentation
- Fails CI if quality is below threshold
- Generates detailed reports
- Comments on pull requests

### Manual Integration

```bash
# In your CI script
python3 tools/doc-quality/doc_quality_check.py --ci --min-score 70 --report report.md
```

## 📈 Reporting

### Console Output
```
📊 Quality Check Results
========================================
Files analyzed: 59/59
Average score: 99.2/100
Score range: 70 - 100
High quality (≥80): 58
Medium quality (60-79): 1
Low quality (<60): 0

✅ All files passed quality check!
```

### Detailed Reports

Generate Markdown reports with:
- Summary statistics
- Top performing files
- Files needing improvement
- Individual file results
- Improvement suggestions

## 🎯 Quality Gates

### Development
- Minimum score: 60 (configurable)
- Warnings for scores <80

### CI/CD
- Fail threshold: 70 (configurable)
- Blocks merges if not met

### Pre-commit
- Checks only staged documentation files
- Can be bypassed with `--no-verify`

## 🔍 Debug and Development Tools

The quality checker includes comprehensive debugging tools to help with development and troubleshooting:

### Debug Options

```bash

# Enable general debug mode
python3 tools/doc-quality/doc_quality_check.py --debug

# Show detailed API request/response information
python3 tools/doc-quality/doc_quality_check.py --debug-api

# Show timing information for all operations
python3 tools/doc-quality/doc_quality_check.py --debug-timing

# Show file discovery and processing details
python3 tools/doc-quality/doc_quality_check.py --debug-files

# Combine multiple debug options
python3 tools/doc-quality/doc_quality_check.py --debug --debug-api --debug-timing --debug-files
```

### Environment Variables

Debug options can also be enabled via environment variables:

```bash
# Enable debug options via environment
export DOC_QUALITY_DEBUG=true
export DOC_QUALITY_DEBUG_API=true
export DOC_QUALITY_DEBUG_TIMING=true
export DOC_QUALITY_DEBUG_FILES=true

# Run with environment-based debug settings
python3 tools/doc-quality/doc_quality_check.py
```

### Save API Responses

Save raw API responses for detailed analysis:

```bash

# Save responses to a directory
python3 tools/doc-quality/doc_quality_check.py --save-responses ./debug_responses

# Each API call creates a timestamped JSON file with:

# - Request details (method, URL, payload)

# - Response details (status, headers, body, timing)
```

### Debug Output Examples

**File Discovery Debug:**
```
🐛 Debug: Searching for documentation files in: docs/
🐛 Debug: File extensions: ['.md', '.txt', '.rst', '.adoc']
🐛 Debug: Found 15 files with extension .md
🐛 Debug: Total files found: 59
```

**Timing Debug:**
```
🐛 Debug: Starting batch analysis with batch_size=10...
🐛 Debug: Analysis completed in 2.345s
🐛 Debug: Average time per file: 0.039s
🐛 Debug: Total API requests made: 12
```

**API Debug:**
```
🐛 Debug: API Request #2: POST <https://api.example.com/analyze/file>
🐛 Debug: Request payload: {"file_path": "/path/to/file.md", "analysis_type": "quality_score"}
🐛 Debug: Response status: 200
🐛 Debug: Response time: 0.123s
🐛 Debug: Response body: {"score": 95, "strength": "Good content", ...}
```

## 📚 API Reference

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--api-url` | Raptor Mini API URL | ngrok URL |
| `--min-score` | Minimum acceptable score | 60 |
| `--report` | Generate detailed report file | None |
| `--ci` | CI mode (exit codes) | False |
| `--batch-size` | Files per batch | 10 |
| `--quiet` | Suppress progress output | False |
| `--json` | JSON output format | False |

### Exit Codes

- `0`: Success
- `1`: Quality check failed
- `2`: Configuration/API error

## 🤝 Contributing

When adding new documentation:

1. Write clear, comprehensive content
2. Test with the quality checker
3. Address any suggestions for improvement
4. Ensure CI passes before merging

## 📞 Support

For issues with:

- **API connectivity**: Check Raptor Mini server status
- **Quality scoring**: Review the analysis output for specific suggestions
- **Configuration**: Validate YAML syntax in `tools/doc-quality/doc_quality_config.yaml`
- **Integration**: Check CI logs and pre-commit hook output
