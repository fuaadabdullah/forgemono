#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class MigrationToolkit {
  constructor(options = {}) {
    this.options = {
      srcPath: options.srcPath || './src',
      dryRun: options.dryRun || false,
      verbose: options.verbose || false,
      output: options.output || './migration-report.html',
      ...options,
    };

    this.stats = {
      filesProcessed: 0,
      filesMigrated: 0,
      patternsApplied: {},
      errors: [],
    };
  }

  log(message, level = 'info') {
    if (level === 'verbose' && !this.options.verbose) return;

    const prefix =
      {
        info: 'ℹ️ ',
        success: '✅ ',
        warning: '⚠️ ',
        error: '❌ ',
      }[level] || '';

    console.log(`${prefix}${message}`);
  }

  findTestFiles() {
    const testFiles = [];

    function scanDirectory(dir) {
      try {
        const items = fs.readdirSync(dir);

        for (const item of items) {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);

          if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
            scanDirectory(fullPath);
          } else if (stat.isFile()) {
            const ext = path.extname(item);
            const name = path.basename(item, ext);

            // Match test files
            if (
              (ext === '.js' || ext === '.jsx' || ext === '.ts' || ext === '.tsx') &&
              (name.endsWith('.test') || name.endsWith('.spec') || item.includes('__tests__'))
            ) {
              testFiles.push(fullPath);
            }
          }
        }
      } catch (error) {
        // Skip directories we can't read
      }
    }

    scanDirectory(this.options.srcPath);
    return testFiles;
  }

  analyzeFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf-8');
    const analysis = {
      usesEnzyme: false,
      patterns: [],
      complexity: 'simple',
    };

    // Check for Enzyme usage
    if (
      content.includes("from 'enzyme'") ||
      content.includes('from "enzyme"') ||
      content.includes('shallow(') ||
      content.includes('mount(')
    ) {
      analysis.usesEnzyme = true;
    }

    // Analyze complexity
    const enzymePatterns = [
      /wrapper\.find\(/g,
      /wrapper\.simulate\(/g,
      /wrapper\.text\(\)/g,
      /wrapper\.prop\(/g,
      /wrapper\.state\(/g,
      /wrapper\.instance\(\)/g,
    ];

    enzymePatterns.forEach((pattern) => {
      const matches = content.match(pattern);
      if (matches) {
        analysis.patterns.push({
          pattern: pattern.source,
          count: matches.length,
        });
      }
    });

    if (analysis.patterns.reduce((sum, p) => sum + p.count, 0) > 10) {
      analysis.complexity = 'complex';
    } else if (analysis.patterns.reduce((sum, p) => sum + p.count, 0) > 5) {
      analysis.complexity = 'medium';
    }

    return analysis;
  }

  applyMigration(filePath, analysis) {
    if (!analysis.usesEnzyme) return false;

    let content = fs.readFileSync(filePath, 'utf-8');
    let changes = [];

    // Migration patterns
    const patterns = [
      {
        name: 'enzyme-imports',
        from: /import\s+{\s*shallow(?:\s*,\s*mount)?\s*}\s+from\s+['"]enzyme['"]/g,
        to: "import { render, screen } from '@testing-library/react';\nimport userEvent from '@testing-library/user-event'",
      },
      {
        name: 'shallow-to-render',
        from: /const\s+(\w+)\s*=\s*shallow\((<[^>]+>)\)/g,
        to: 'render($2)',
      },
      {
        name: 'mount-to-render',
        from: /const\s+(\w+)\s*=\s*mount\((<[^>]+>)\)/g,
        to: 'render($2)',
      },
      {
        name: 'find-button',
        from: /(\w+)\.find\(['"]button['"]\)/g,
        to: "screen.getByRole('button')",
      },
      {
        name: 'find-input',
        from: /(\w+)\.find\(['"]input['"]\)/g,
        to: "screen.getByRole('textbox')",
      },
      {
        name: 'simulate-click',
        from: /\.simulate\(['"]click['"]\)/g,
        to: '.click()',
      },
      {
        name: 'simulate-change',
        from: /\.simulate\(['"]change['"],\s*{\s*target:\s*{\s*value:\s*([^}]+)\s*}\s*}\)/g,
        to: '.type($1)',
      },
    ];

    patterns.forEach((pattern) => {
      const newContent = content.replace(pattern.from, pattern.to);
      if (newContent !== content) {
        changes.push(pattern.name);
        content = newContent;
        this.stats.patternsApplied[pattern.name] =
          (this.stats.patternsApplied[pattern.name] || 0) + 1;
      }
    });

    // Add userEvent setup for async tests
    if (content.includes('userEvent.') && !content.includes('userEvent.setup()')) {
      const asyncTestRegex = /(test|it)\(['"]([^'"]+)['"],\s*async\s*\(\)\s*=>\s*{/g;
      content = content.replace(asyncTestRegex, (match) => {
        return match.replace(
          /async\s*\(\)\s*=>\s*{/,
          'async () => {\n  const user = userEvent.setup();'
        );
      });
      changes.push('userEvent-setup');
    }

    if (changes.length > 0) {
      if (!this.options.dryRun) {
        fs.writeFileSync(filePath, content);
      }
      this.log(`${path.relative(process.cwd(), filePath)}: ${changes.join(', ')}`, 'success');
      return true;
    }

    return false;
  }

  generateHtmlReport() {
    const template = `
<!DOCTYPE html>
<html>
<head>
  <title>Testing Library Migration Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    .summary { background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
    .stats { display: flex; gap: 20px; margin-bottom: 20px; }
    .stat { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .patterns { margin-top: 20px; }
    .pattern { background: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 4px solid #007acc; }
    .errors { color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 8px; margin-top: 20px; }
  </style>
</head>
<body>
  <h1>🧪 Testing Library Migration Report</h1>
  <div class="summary">
    <h2>Summary</h2>
    <div class="stats">
      <div class="stat">
        <h3>${this.stats.filesProcessed}</h3>
        <p>Files Processed</p>
      </div>
      <div class="stat">
        <h3>${this.stats.filesMigrated}</h3>
        <p>Files Migrated</p>
      </div>
      <div class="stat">
        <h3>${Object.keys(this.stats.patternsApplied).length}</h3>
        <p>Patterns Applied</p>
      </div>
    </div>
  </div>

  <h2>Applied Patterns</h2>
  <div class="patterns">
    ${Object.entries(this.stats.patternsApplied)
      .map(([pattern, count]) => `<div class="pattern">${pattern}: ${count} times</div>`)
      .join('')}
  </div>

  ${
    this.stats.errors.length > 0
      ? `
  <div class="errors">
    <h2>Errors</h2>
    ${this.stats.errors.map((error) => `<p>${error}</p>`).join('')}
  </div>
  `
      : ''
  }

  <p><em>Generated on ${new Date().toLocaleString()}</em></p>
</body>
</html>`;

    fs.writeFileSync(this.options.output, template);
    this.log(`Report saved to ${this.options.output}`, 'success');
  }

  async run() {
    this.log('🔍 Finding test files...');
    const testFiles = this.findTestFiles();
    this.log(`📁 Found ${testFiles.length} test files`);

    if (testFiles.length === 0) {
      this.log("No test files found. Make sure you're in the right directory.", 'warning');
      return;
    }

    this.log('🚀 Starting migration analysis...');

    for (const file of testFiles) {
      try {
        this.stats.filesProcessed++;
        const analysis = this.analyzeFile(file);

        if (this.options.verbose) {
          this.log(
            `Analyzed ${path.relative(process.cwd(), file)}: ${analysis.usesEnzyme ? 'uses Enzyme' : 'no Enzyme'} (${analysis.complexity})`,
            'verbose'
          );
        }

        if (this.applyMigration(file, analysis)) {
          this.stats.filesMigrated++;
        }
      } catch (error) {
        this.stats.errors.push(`${file}: ${error.message}`);
        this.log(`Error processing ${file}: ${error.message}`, 'error');
      }
    }

    this.log(`\n✅ Migration complete!`, 'success');
    this.log(`📈 ${this.stats.filesMigrated}/${this.stats.filesProcessed} files migrated`);

    this.generateHtmlReport();

    if (this.stats.filesMigrated > 0) {
      this.log('\n💡 Next steps:', 'info');
      this.log('1. Review migrated files manually', 'info');
      this.log('2. Run tests to ensure functionality is preserved', 'info');
      this.log('3. Consider adding @testing-library/jest-dom for additional matchers', 'info');
    }
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const options = {};

  // Parse arguments
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--src':
      case '-s':
        options.srcPath = args[++i];
        break;
      case '--dry-run':
        options.dryRun = true;
        break;
      case '--verbose':
      case '-v':
        options.verbose = true;
        break;
      case '--output':
      case '-o':
        options.output = args[++i];
        break;
      case '--help':
      case '-h':
        console.log(`
Testing Library Migration Toolkit

Usage: node migrate-tests.js [options]

Options:
  -s, --src <path>     Source path to scan (default: ./src)
  --dry-run           Show what would be changed without making changes
  -v, --verbose       Verbose output
  -o, --output <file> Output report file (default: ./migration-report.html)
  -h, --help          Show this help

Examples:
  node migrate-tests.js --dry-run --verbose
  node migrate-tests.js --src ./tests --output ./report.html
        `);
        process.exit(0);
    }
  }

  const toolkit = new MigrationToolkit(options);
  await toolkit.run();
}

if (require.main === module) {
  main().catch((error) => {
    console.error('❌ Migration failed:', error.message);
    process.exit(1);
  });
}

module.exports = MigrationToolkit;
