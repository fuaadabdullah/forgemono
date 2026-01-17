const fs = require('fs');
const path = require('path');
const Table = require('cli-table3');
const chalk = require('chalk');

class MigrationDashboard {
  constructor() {
    this.stats = {
      total: 0,
      migrated: 0,
      byType: {},
      blockers: [],
      estimatedTime: 0,
      lastScan: null,
    };
  }

  scan(projectRoot = process.cwd()) {
    console.log(chalk.cyan('🔍 Scanning for test files...\n'));

    const testFiles = this.findTestFiles(projectRoot);
    this.stats.total = testFiles.length;
    this.stats.lastScan = new Date();

    console.log(chalk.blue(`📊 Found ${testFiles.length} test files\n`));

    testFiles.forEach((file) => {
      const content = fs.readFileSync(file, 'utf-8');
      const isMigrated = this.isMigrated(content);
      const type = this.classifyTest(file, content);
      const complexity = this.calculateComplexity(content);

      if (isMigrated) {
        this.stats.migrated++;
        this.stats.byType[type] = (this.stats.byType[type] || 0) + 1;
      } else if (complexity > 50) {
        this.stats.blockers.push({ file, complexity, type });
      }
    });

    this.calculateETA();
    this.display();
  }

  findTestFiles(rootDir) {
    const testFiles = [];

    function scan(dir) {
      try {
        const items = fs.readdirSync(dir);

        items.forEach((item) => {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);

          if (stat.isDirectory() && !this.shouldSkipDir(item)) {
            scan.call(this, fullPath);
          } else if (stat.isFile() && this.isTestFile(item)) {
            testFiles.push(fullPath);
          }
        });
      } catch (error) {
        // Skip directories we can't read
      }
    }

    scan.call(this, rootDir);
    return testFiles;
  }

  shouldSkipDir(dirName) {
    const skipDirs = [
      'node_modules',
      '.git',
      'dist',
      'build',
      'coverage',
      '__pycache__',
      '.next',
      '.nuxt',
      'target',
      'bin',
    ];
    return skipDirs.includes(dirName) || dirName.startsWith('.');
  }

  isTestFile(fileName) {
    return /\.(test|spec)\.(js|jsx|ts|tsx)$/.test(fileName);
  }

  isMigrated(content) {
    // Check for Enzyme usage
    const enzymePatterns = [
      /import\s*{\s*shallow\s*}/,
      /import\s*{\s*mount\s*}/,
      /from\s+['"]enzyme['"]/,
      /\.find\(.*\)\.simulate\(/,
      /wrapper\.find\(/,
      /wrapper\.props\(\)/,
      /wrapper\.state\(/,
    ];

    return !enzymePatterns.some((pattern) => pattern.test(content));
  }

  classifyTest(filePath, content) {
    const fileName = path.basename(filePath).toLowerCase();

    // Component tests
    if (
      fileName.includes('component') ||
      fileName.includes('button') ||
      fileName.includes('input') ||
      fileName.includes('form')
    ) {
      return 'component';
    }

    // Utility/helper tests
    if (
      fileName.includes('util') ||
      fileName.includes('helper') ||
      fileName.includes('format') ||
      fileName.includes('validate')
    ) {
      return 'utility';
    }

    // Hook tests
    if (fileName.includes('hook') || fileName.includes('use')) {
      return 'hook';
    }

    // Integration tests
    if (content.includes('render') && content.includes('screen.getBy')) {
      return 'integration';
    }

    return 'unit';
  }

  calculateComplexity(content) {
    let complexity = 0;

    // Enzyme patterns (higher complexity to migrate)
    if (content.includes('mount(')) complexity += 20;
    if (content.includes('.state(')) complexity += 15;
    if (content.includes('.instance()')) complexity += 15;
    if (content.includes('.props()')) complexity += 10;
    if (content.includes('shallow(')) complexity += 5;

    // Multiple interactions
    const interactionCount = (content.match(/\.simulate\(/g) || []).length;
    complexity += interactionCount * 3;

    // Async patterns
    if (content.includes('async') || content.includes('await')) complexity += 5;

    // Complex selectors
    const complexSelectors = (content.match(/\.find\([^)]+\.class/g) || []).length;
    complexity += complexSelectors * 5;

    return Math.min(complexity, 100);
  }

  calculateETA() {
    const remaining = this.stats.total - this.stats.migrated;
    const avgTimePerTest = 8; // minutes
    this.stats.estimatedTime = remaining * avgTimePerTest;
  }

  display() {
    const table = new Table({
      head: ['Metric', 'Value', 'Progress'],
      colWidths: [25, 15, 25],
      style: { head: ['cyan'] },
    });

    const progress =
      this.stats.total > 0 ? ((this.stats.migrated / this.stats.total) * 100).toFixed(1) : 0;

    table.push(
      ['Total Tests', this.stats.total.toString(), ''],
      ['Migrated', this.stats.migrated.toString(), `${progress}%`],
      ['Remaining', (this.stats.total - this.stats.migrated).toString(), ''],
      ['ETA', this.formatTime(this.stats.estimatedTime), ''],
      [
        'Blockers',
        this.stats.blockers.length.toString(),
        this.stats.blockers.length > 0 ? '⚠️' : '✅',
      ]
    );

    console.log(chalk.green.bold('\n📊 Migration Dashboard\n'));
    console.log(table.toString());

    // Show breakdown by type
    if (Object.keys(this.stats.byType).length > 0) {
      console.log(chalk.blue.bold('\n📈 Migration by Type:'));
      Object.entries(this.stats.byType).forEach(([type, count]) => {
        const percentage = ((count / this.stats.migrated) * 100).toFixed(1);
        console.log(`  ${type}: ${count} tests (${percentage}%)`);
      });
    }

    // Show blockers
    if (this.stats.blockers.length > 0) {
      console.log(chalk.yellow.bold('\n🚨 Complex Tests (Need Attention):'));
      this.stats.blockers.slice(0, 5).forEach(({ file, complexity, type }) => {
        const relativePath = path.relative(process.cwd(), file);
        console.log(`  ${relativePath} (${type}) - complexity: ${complexity}`);
      });

      if (this.stats.blockers.length > 5) {
        console.log(`  ... and ${this.stats.blockers.length - 5} more`);
      }
    }

    // Show recommendations
    this.showRecommendations();

    console.log(chalk.gray(`\n📅 Last scan: ${this.stats.lastScan.toLocaleString()}`));
  }

  formatTime(minutes) {
    if (minutes < 60) {
      return `${Math.ceil(minutes)} minutes`;
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = Math.ceil(minutes % 60);
      return `${hours}h ${remainingMinutes}m`;
    }
  }

  showRecommendations() {
    console.log(chalk.magenta.bold('\n💡 Recommendations:'));

    const progress = (this.stats.migrated / this.stats.total) * 100;

    if (progress < 25) {
      console.log('  • Start with simple component tests (Button, Input)');
      console.log('  • Use turbo migration for low-complexity tests');
    } else if (progress < 50) {
      console.log('  • Focus on form components and user interactions');
      console.log('  • Consider parallel migration for team efficiency');
    } else if (progress < 75) {
      console.log('  • Tackle complex stateful components');
      console.log('  • Review integration tests for migration opportunities');
    } else {
      console.log('  • Focus on remaining blockers and edge cases');
      console.log('  • Run full test suite validation');
    }

    if (this.stats.blockers.length > 0) {
      console.log('  • Address high-complexity tests with team review');
    }
  }
}

// CLI interface
function main() {
  const args = process.argv.slice(2);
  const projectRoot = args[0] || process.cwd();

  const dashboard = new MigrationDashboard();
  dashboard.scan(projectRoot);
}

// Export for use as module
module.exports = MigrationDashboard;

// Run if called directly
if (require.main === module) {
  main();
}
