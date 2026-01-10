#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const MIGRATION_ORDER = [
  {
    type: 'utils',
    pattern: /\/utils\/.*\.test\./,
    priority: 1, // Easiest, no React
    timeEstimate: '5min each',
    description: 'Utility functions, pure functions, no React components',
  },
  {
    type: 'hooks',
    pattern: /\/hooks\/.*\.test\./,
    priority: 2,
    timeEstimate: '10min each',
    description: 'Custom React hooks, state management',
  },
  {
    type: 'presentational',
    pattern: /\/components\/(ui|common|atoms|molecules)\/.*\.test\./,
    priority: 3,
    timeEstimate: '15min each',
    description: 'Simple UI components, no complex logic',
  },
  {
    type: 'container',
    pattern: /\/components\/(containers|features|organisms)\/.*\.test\./,
    priority: 4,
    timeEstimate: '30min each',
    description: 'Complex components with state, effects, API calls',
  },
  {
    type: 'pages',
    pattern: /\/(pages|views|screens)\/.*\.test\./,
    priority: 5,
    timeEstimate: '45min each',
    description: 'Page-level components, routing, complex interactions',
  },
  {
    type: 'integration',
    pattern: /\/__tests__\/(integration|e2e)\/.*\.test\./,
    priority: 6,
    timeEstimate: '60min each',
    description: 'Integration tests, multiple components, full workflows',
  },
];

class ParallelMigrator {
  constructor(options = {}) {
    this.options = {
      srcPath: options.srcPath || './src',
      batchSize: options.batchSize || 5,
      dryRun: options.dryRun || false,
      focusType: options.focusType || null,
      ...options,
    };

    this.stats = {
      totalFiles: 0,
      byType: {},
      migrated: 0,
      skipped: 0,
      errors: [],
    };
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

  classifyFile(filePath) {
    const relativePath = path.relative(process.cwd(), filePath);

    for (const category of MIGRATION_ORDER) {
      if (category.pattern.test(relativePath)) {
        return category;
      }
    }

    // Default classification
    return {
      type: 'unknown',
      pattern: /.*/,
      priority: 99,
      timeEstimate: 'unknown',
      description: 'Unclassified test file',
    };
  }

  analyzeFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const analysis = {
        usesEnzyme: false,
        usesReact: false,
        lines: content.split('\n').length,
        imports: [],
        testCount: 0,
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

      // Check for React usage
      if (content.includes('React') || content.includes('jsx') || content.includes('<')) {
        analysis.usesReact = true;
      }

      // Count tests
      const testMatches = content.match(/(describe|test|it)\s*\(/g);
      analysis.testCount = testMatches ? testMatches.length : 0;

      // Estimate complexity
      if (analysis.lines > 200) analysis.complexity = 'complex';
      else if (analysis.lines > 100) analysis.complexity = 'medium';

      return analysis;
    } catch (error) {
      return { error: error.message };
    }
  }

  generateMigrationPlan() {
    console.log('🔍 Analyzing test files for migration plan...\n');

    const testFiles = this.findTestFiles();
    this.stats.totalFiles = testFiles.length;

    const categorized = {};

    for (const file of testFiles) {
      const category = this.classifyFile(file);
      const analysis = this.analyzeFile(file);

      if (!categorized[category.type]) {
        categorized[category.type] = {
          category,
          files: [],
          stats: { total: 0, enzyme: 0, react: 0, tests: 0 },
        };
      }

      categorized[category.type].files.push({
        path: file,
        analysis,
        relativePath: path.relative(process.cwd(), file),
      });

      categorized[category.type].stats.total++;
      if (analysis.usesEnzyme) categorized[category.type].stats.enzyme++;
      if (analysis.usesReact) categorized[category.type].stats.react++;
      categorized[category.type].stats.tests += analysis.testCount || 0;
    }

    return categorized;
  }

  displayMigrationPlan(categorized) {
    console.log('📋 MIGRATION PLAN\n');
    console.log('═'.repeat(80));

    const sortedCategories = Object.values(categorized).sort(
      (a, b) => a.category.priority - b.category.priority
    );

    for (const { category, files, stats } of sortedCategories) {
      if (this.options.focusType && category.type !== this.options.focusType) continue;

      console.log(`\n🎯 ${category.type.toUpperCase()} (Priority ${category.priority})`);
      console.log(`   ${category.description}`);
      console.log(`   Est. time: ${category.timeEstimate} per file`);
      console.log(`   Files: ${stats.total} (${stats.enzyme} need migration)`);
      console.log(`   Tests: ${stats.tests}`);

      if (stats.enzyme > 0) {
        console.log(`   📁 Files to migrate:`);
        files
          .filter((f) => f.analysis.usesEnzyme)
          .slice(0, 5) // Show first 5
          .forEach((f) => {
            const complexity = f.analysis.complexity;
            const testCount = f.analysis.testCount;
            console.log(`      • ${f.relativePath} (${complexity}, ${testCount} tests)`);
          });

        const remaining = stats.enzyme - 5;
        if (remaining > 0) {
          console.log(`      ... and ${remaining} more`);
        }
      }

      console.log('');
    }

    // Summary
    const totalEnzyme = Object.values(categorized).reduce((sum, cat) => sum + cat.stats.enzyme, 0);

    console.log('═'.repeat(80));
    console.log(`📊 SUMMARY`);
    console.log(`   Total files: ${this.stats.totalFiles}`);
    console.log(`   Need migration: ${totalEnzyme}`);
    console.log(`   Estimated total time: ${this.estimateTotalTime(categorized)}`);
    console.log('');
  }

  estimateTotalTime(categorized) {
    let totalMinutes = 0;

    for (const { category, stats } of Object.values(categorized)) {
      const timePerFile = parseInt(category.timeEstimate.replace('min', ''));
      totalMinutes += stats.enzyme * timePerFile;
    }

    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  }

  async migrateBatch(files, category) {
    console.log(`\n🚀 Migrating ${files.length} ${category.type} files...`);

    let migrated = 0;
    let errors = 0;

    for (const file of files) {
      try {
        const migratedFile = await this.migrateFile(file.path, category);
        if (migratedFile) {
          migrated++;
          console.log(`   ✅ ${path.relative(process.cwd(), file.path)}`);
        } else {
          console.log(`   ⏭️  ${path.relative(process.cwd(), file.path)} (no changes needed)`);
        }
      } catch (error) {
        errors++;
        console.log(`   ❌ ${path.relative(process.cwd(), file.path)}: ${error.message}`);
        this.stats.errors.push(`${file.path}: ${error.message}`);
      }
    }

    console.log(`\n📈 Batch complete: ${migrated} migrated, ${errors} errors`);
    return { migrated, errors };
  }

  async migrateFile(filePath, category) {
    // Use the existing turbo-migrate logic
    const turboMigrate = require('./turbo-migrate.js');

    if (typeof turboMigrate.turboMigrateFile === 'function') {
      return turboMigrate.turboMigrateFile(filePath);
    }

    // Fallback: simple migration
    let content = fs.readFileSync(filePath, 'utf-8');
    let changed = false;

    // Basic Enzyme → Testing Library conversions
    const conversions = [
      [
        /import\s+{\s*shallow\s*}\s+from\s+['"]enzyme['"]/g,
        "import { render, screen } from '@testing-library/react'",
      ],
      [/const\s+(\w+)\s*=\s*shallow\(/g, 'render('],
      [/(\w+)\.find\(['"]([^'"]+)['"]\)/g, "screen.getByRole('$2')"],
      [/(\w+)\.simulate\(['"]click['"]\)/g, "await user.click(screen.getByRole('button'))"],
    ];

    conversions.forEach(([pattern, replacement]) => {
      if (pattern.test(content)) {
        content = content.replace(pattern, replacement);
        changed = true;
      }
    });

    if (changed && !this.options.dryRun) {
      fs.writeFileSync(filePath, content);
    }

    return changed;
  }

  async runMigration(categorized) {
    if (this.options.dryRun) {
      console.log('\n🔍 DRY RUN - No files will be modified\n');
    }

    const sortedCategories = Object.values(categorized).sort(
      (a, b) => a.category.priority - b.category.priority
    );

    for (const { category, files } of sortedCategories) {
      if (this.options.focusType && category.type !== this.options.focusType) continue;

      const enzymeFiles = files.filter((f) => f.analysis.usesEnzyme);
      if (enzymeFiles.length === 0) continue;

      // Process in batches
      for (let i = 0; i < enzymeFiles.length; i += this.options.batchSize) {
        const batch = enzymeFiles.slice(i, i + this.options.batchSize);
        await this.migrateBatch(batch, category);

        if (i + this.options.batchSize < enzymeFiles.length) {
          console.log(`⏸️  Batch complete. Press Enter to continue with next batch...`);
          await new Promise((resolve) => process.stdin.once('data', resolve));
        }
      }
    }
  }

  generateReport(categorized) {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalFiles: this.stats.totalFiles,
        categories: Object.keys(categorized).length,
        totalEnzymeFiles: Object.values(categorized).reduce(
          (sum, cat) => sum + cat.stats.enzyme,
          0
        ),
        estimatedTime: this.estimateTotalTime(categorized),
      },
      categories: {},
      errors: this.stats.errors,
    };

    for (const [type, data] of Object.entries(categorized)) {
      report.categories[type] = {
        priority: data.category.priority,
        description: data.category.description,
        timeEstimate: data.category.timeEstimate,
        stats: data.stats,
        files: data.files
          .filter((f) => f.analysis.usesEnzyme)
          .map((f) => ({
            path: f.relativePath,
            complexity: f.analysis.complexity,
            testCount: f.analysis.testCount,
            lines: f.analysis.lines,
          })),
      };
    }

    const reportPath = './migration-plan-report.json';
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`📊 Detailed report saved to ${reportPath}`);
  }

  async run() {
    const categorized = this.generateMigrationPlan();
    this.displayMigrationPlan(categorized);

    if (!this.options.dryRun) {
      const readline = require('readline');
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
      });

      const answer = await new Promise((resolve) => {
        rl.question('🚀 Start migration? (y/N): ', resolve);
      });

      rl.close();

      if (answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes') {
        await this.runMigration(categorized);
      } else {
        console.log('Migration cancelled.');
        return;
      }
    }

    this.generateReport(categorized);
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
      case '--batch-size':
        options.batchSize = parseInt(args[++i]);
        break;
      case '--dry-run':
        options.dryRun = true;
        break;
      case '--focus-type':
        options.focusType = args[++i];
        break;
      case '--help':
      case '-h':
        console.log(`
Parallel Migration by Test Type

Usage: node scripts/migrate-by-type.js [options]

Options:
  -s, --src <path>         Source path (default: ./src)
  --batch-size <num>       Files to migrate per batch (default: 5)
  --dry-run                Show plan without migrating
  --focus-type <type>      Only migrate specific type (utils, hooks, etc.)
  -h, --help               Show this help

Examples:
  node scripts/migrate-by-type.js --dry-run
  node scripts/migrate-by-type.js --focus-type utils
  node scripts/migrate-by-type.js --batch-size 3
        `);
        process.exit(0);
    }
  }

  const migrator = new ParallelMigrator(options);
  await migrator.run();
}

if (require.main === module) {
  main().catch((error) => {
    console.error('❌ Migration failed:', error.message);
    process.exit(1);
  });
}

module.exports = ParallelMigrator;
