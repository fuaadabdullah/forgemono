// ROI Calculator for Enzyme to Testing Library Migration
const Table = require('cli-table3');
const chalk = require('chalk');

class MigrationROI {
  constructor() {
    // Time estimates in minutes per test
    this.TIME_ESTIMATES = {
      manual: {
        simple: 15, // minutes per simple test
        medium: 30, // minutes per medium test
        complex: 60, // minutes per complex test
        monster: 120, // minutes per monster test
      },
      automated: {
        simple: 2, // minutes per simple test (turbo mode)
        medium: 5, // minutes per medium test
        complex: 15, // minutes per complex test
        monster: 30, // minutes per monster test (with AI assistance)
      },
    };

    // Developer hourly rates (USD)
    this.HOURLY_RATES = {
      junior: 50,
      mid: 75,
      senior: 100,
      principal: 125,
    };
  }

  calculateROI(testCounts, options = {}) {
    const {
      developerLevel = 'mid',
      includeTraining = true,
      includeTesting = true,
      parallelFactor = 1,
    } = options;

    console.log(chalk.cyan.bold('\n📊 Migration ROI Calculator\n'));

    let manualTime = 0;
    let automatedTime = 0;
    let totalTests = 0;

    // Calculate times for each complexity level
    Object.entries(testCounts).forEach(([type, count]) => {
      if (count > 0) {
        manualTime += count * this.TIME_ESTIMATES.manual[type];
        automatedTime += count * this.TIME_ESTIMATES.automated[type];
        totalTests += count;
      }
    });

    // Apply parallel factor (team size)
    automatedTime = automatedTime / parallelFactor;

    // Add training time (one-time cost)
    if (includeTraining) {
      manualTime += 120; // 2 hours training for manual approach
      automatedTime += 30; // 30 minutes training for automated approach
    }

    // Add testing/validation time
    if (includeTesting) {
      manualTime += totalTests * 5; // 5 minutes testing per test manually
      automatedTime += totalTests * 1; // 1 minute validation per test automated
    }

    const timeSaved = manualTime - automatedTime;
    const percentFaster = manualTime > 0 ? ((manualTime / automatedTime) * 100).toFixed(0) : 0;

    const hourlyRate = this.HOURLY_RATES[developerLevel];
    const costSavings = (timeSaved / 60) * hourlyRate;

    return {
      totalTests,
      manualTime: this.formatTime(manualTime),
      automatedTime: this.formatTime(automatedTime),
      timeSaved: this.formatTime(timeSaved),
      percentFaster: `${percentFaster}%`,
      costSavings: `$${costSavings.toFixed(0)}`,
      hourlyRate,
      breakdown: this.createBreakdownTable(testCounts, manualTime, automatedTime),
    };
  }

  createBreakdownTable(testCounts, manualTime, automatedTime) {
    const table = new Table({
      head: ['Complexity', 'Count', 'Manual Time', 'Auto Time', 'Time Saved'],
      colWidths: [15, 10, 15, 15, 15],
      style: { head: ['cyan'] },
    });

    Object.entries(testCounts).forEach(([type, count]) => {
      if (count > 0) {
        const manual = count * this.TIME_ESTIMATES.manual[type];
        const automated = count * this.TIME_ESTIMATES.automated[type];
        const saved = manual - automated;

        table.push([
          type,
          count.toString(),
          this.formatTime(manual),
          this.formatTime(automated),
          this.formatTime(saved),
        ]);
      }
    });

    return table;
  }

  formatTime(minutes) {
    if (minutes < 60) {
      return `${Math.round(minutes)}m`;
    } else if (minutes < 480) {
      // 8 hours
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = Math.round(minutes % 60);
      return `${hours}h ${remainingMinutes}m`;
    } else {
      const days = Math.floor(minutes / 480);
      const hours = Math.floor((minutes % 480) / 60);
      return `${days}d ${hours}h`;
    }
  }

  showComparison(roi) {
    console.log(chalk.green.bold('💰 Cost Comparison:'));
    console.log(`   Manual Approach: ${roi.manualTime} @ $${roi.hourlyRate}/hr`);
    console.log(`   Automated Approach: ${roi.automatedTime} @ $${roi.hourlyRate}/hr`);
    console.log(chalk.green(`   Time Saved: ${roi.timeSaved} (${roi.percentFaster} faster)`));
    console.log(chalk.green(`   Cost Savings: ${roi.costSavings}`));

    console.log('\n📈 Detailed Breakdown:');
    console.log(roi.breakdown.toString());
  }

  // Preset scenarios
  getPresetScenarios() {
    return {
      small: { simple: 20, medium: 10, complex: 5, monster: 1 },
      medium: { simple: 100, medium: 50, complex: 20, monster: 5 },
      large: { simple: 500, medium: 200, complex: 100, monster: 25 },
      enterprise: { simple: 2000, medium: 800, complex: 400, monster: 100 },
    };
  }

  showPresetComparison() {
    console.log(chalk.yellow.bold('\n🏢 Preset Scenario Comparison:\n'));

    const presets = this.getPresetScenarios();
    const scenarios = ['small', 'medium', 'large', 'enterprise'];

    scenarios.forEach((scenario) => {
      const counts = presets[scenario];
      const roi = this.calculateROI(counts, { developerLevel: 'mid', parallelFactor: 1 });

      console.log(chalk.cyan(`${scenario.toUpperCase()} PROJECT (${roi.totalTests} tests):`));
      console.log(`   Manual: ${roi.manualTime} | Automated: ${roi.automatedTime}`);
      console.log(
        `   Savings: ${roi.timeSaved} (${roi.percentFaster} faster) | Cost: ${roi.costSavings}`
      );
      console.log('');
    });
  }
}

// CLI interface
function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'interactive';

  const calculator = new MigrationROI();

  if (command === 'presets') {
    calculator.showPresetComparison();
  } else if (command === 'calculate') {
    // Parse test counts from args: --simple=100 --medium=50 --complex=20 --monster=5
    const testCounts = { simple: 0, medium: 0, complex: 0, monster: 0 };

    args.forEach((arg) => {
      const match = arg.match(/--(\w+)=(\d+)/);
      if (match) {
        const [, type, count] = match;
        if (testCounts.hasOwnProperty(type)) {
          testCounts[type] = parseInt(count);
        }
      }
    });

    const roi = calculator.calculateROI(testCounts);
    calculator.showComparison(roi);
  } else {
    // Interactive mode
    console.log(chalk.blue('Enter your test counts for ROI calculation:\n'));

    // For simplicity, we'll use preset scenarios in CLI
    calculator.showPresetComparison();

    console.log(chalk.gray('Usage:'));
    console.log('  node roi-calculator.js presets                    # Show preset scenarios');
    console.log(
      '  node roi-calculator.js calculate --simple=100 --medium=50 --complex=20 --monster=5'
    );
  }
}

// Export for use as module
module.exports = MigrationROI;

// Run if called directly
if (require.main === module) {
  main();
}
