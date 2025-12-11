# Goblin Assistant Mini - Standalone Documentation Quality Checker

A standalone version of the documentation quality analysis tool that works without external dependencies, featuring both local LLM analysis and heuristic fallbacks.

## Features

- **Local LLM Support**: Uses Phi-3 or other local models when available
- **Zero External Dependencies**: No network calls or external APIs required
- **Intelligent Fallback**: Falls back to heuristic analysis if LLMs aren't available
- **Comprehensive Scoring**: Analyzes structure, content depth, readability, and formatting
- **Truly Standalone**: Works with just Python and optional local models

## How It Works

The standalone mode follows this priority order:

1. **Local LLM Analysis** (if available)
   - Uses Phi-3 mini or other local models
   - Provides AI-powered quality analysis
   - Runs completely offline

2. **Heuristic Analysis** (fallback)
   - Rule-based quality scoring
   - No external dependencies
   - Always available

## Setup

### With Local LLMs (Recommended)

```bash
# Install local model support
pip install llama-cpp-python aiohttp

# Download Phi-3 model (place in models/ directory)
# The tool will automatically detect and use local models
```

### Without Local LLMs (Minimal)

```bash
# Just Python - no additional dependencies required
# Will use heuristic analysis automatically
python3 tools/doc-quality/doc_quality_check.py --standalone
```

## Quick Start

### Basic Usage

```bash
# Analyze all documentation files
python3 tools/doc-quality/doc_quality_check.py --standalone

# Analyze specific files
python3 tools/doc-quality/doc_quality_check.py docs/*.md --standalone

# Get JSON output for automation
python3 tools/doc-quality/doc_quality_check.py --standalone --json

# Quiet mode for CI/CD
python3 tools/doc-quality/doc_quality_check.py --standalone --quiet
```

### Quality Metrics

The standalone analyzer evaluates documentation based on:

- **Content Length**: Longer, more comprehensive content scores higher
- **Structure**: Presence of headers, lists, and proper formatting
- **Readability**: Sentence length and word complexity analysis
- **Code Examples**: Bonus points for included code snippets

### Score Ranges

- **80-100**: High quality documentation
- **60-79**: Medium quality - needs some improvements
- **<60**: Low quality - significant improvements needed

## Comparison with Full Version

| Feature | Standalone Mode | Full Version |
|---------|----------------|--------------|
| Dependencies | None | Virtual env + APIs |
| Speed | Instant | Network-dependent |
| Accuracy | Heuristic-based | AI-powered analysis |
| Setup | Just Python | Complex infrastructure |
| Reliability | Always works | Requires external services |

## Use Cases

### Development
- Quick quality checks during writing
- CI/CD pipelines without external dependencies
- Offline documentation review

### Production
- Automated quality gates
- Documentation maintenance
- Quality trend monitoring

## Configuration

The standalone mode uses built-in heuristics and doesn't require configuration files. All analysis is performed locally using standard Python libraries.

## Troubleshooting

### Common Issues

**Low Scores on Good Documentation**
- The heuristic analyzer may not recognize specialized content
- Consider using the full version for complex documentation

**Import Errors**
- Ensure you're using Python 3.6+
- The tool only requires standard library modules

**Performance Issues**
- Standalone mode is very fast (< 1 second per file)
- If you need slower, more accurate analysis, use the full version

## Integration

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Check Documentation Quality
  run: |
    python3 tools/doc-quality/doc_quality_check.py --standalone --ci --min-score 70
```

### Pre-commit Hooks

```bash
# Add to .pre-commit-config.yaml
- repo: local
  hooks:
  - id: doc-quality
    name: Documentation Quality Check
    entry: python3 tools/doc-quality/doc_quality_check.py --standalone --ci
    language: system
    files: \.md$
```

## Contributing

The standalone analyzer uses simple, maintainable heuristics. To improve scoring accuracy:

1. Analyze failing cases
2. Adjust scoring weights in `StandaloneQualityChecker`
3. Test with diverse documentation samples
4. Ensure backward compatibility

## License

Same as the main ForgeMonorepo project.
