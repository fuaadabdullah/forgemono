#!/usr/bin/env node
const inquirer = require('inquirer');
const fs = require('fs');
const path = require('path');
const chalk = require('chalk');

console.log(chalk.cyan('🚀 Interactive Test Migration\n'));

async function main() {
  const answers = await inquirer.prompt([
    {
      type: 'list',
      name: 'strategy',
      message: 'Choose migration strategy:',
      choices: [
        { name: '⚡ Turbo (Auto-fix all patterns)', value: 'turbo' },
        { name: '🧠 Smart (AI-assisted)', value: 'smart' },
        { name: '🎯 Targeted (Component by component)', value: 'targeted' },
        { name: '📊 Report first (Analyze then migrate)', value: 'analyze' },
      ],
    },
    {
      type: 'checkbox',
      name: 'components',
      message: 'Select components to migrate:',
      choices: getComponentList(),
      when: (answers) => answers.strategy === 'targeted',
    },
    {
      type: 'confirm',
      name: 'backup',
      message: 'Create backup before migration?',
      default: true,
    },
    {
      type: 'confirm',
      name: 'dryRun',
      message: 'Run in dry-run mode first?',
      default: true,
      when: (answers) => answers.strategy !== 'analyze',
    },
  ]);

  console.log(`\nStarting ${answers.strategy} migration...`);

  if (answers.backup) {
    console.log(chalk.yellow('📦 Creating backup...'));
    await createBackup();
  }

  switch (answers.strategy) {
    case 'turbo':
      await runTurboMigration(answers.dryRun);
      break;
    case 'smart':
      await runSmartMigration(answers.dryRun);
      break;
    case 'targeted':
      await runTargetedMigration(answers.components, answers.dryRun);
      break;
    case 'analyze':
      await runAnalysis();
      break;
  }

  console.log(chalk.green('\n✅ Migration complete!'));
}

function getComponentList() {
  const components = [];

  try {
    // Scan for components with tests in common locations
    const searchPaths = [
      './src/components',
      './components',
      './apps/goblin-assistant/src/components',
      './apps/goblin-assistant/components',
    ];

    searchPaths.forEach((searchPath) => {
      if (fs.existsSync(searchPath)) {
        fs.readdirSync(searchPath).forEach((folder) => {
          const componentPath = path.join(searchPath, folder);
          if (fs.statSync(componentPath).isDirectory()) {
            // Look for test files
            const testPatterns = [
              `${folder}.test.tsx`,
              `${folder}.test.ts`,
              `${folder}.test.js`,
              `${folder}.spec.tsx`,
              `${folder}.spec.ts`,
              `${folder}.spec.js`,
            ];

            const hasTest = testPatterns.some((pattern) => {
              const testFile = path.join(componentPath, pattern);
              return fs.existsSync(testFile);
            });

            if (hasTest) {
              components.push({ name: folder, value: folder });
            }
          }
        });
      }
    });
  } catch (error) {
    console.log(
      chalk.yellow('⚠️  Could not scan for components, proceeding without component list')
    );
  }

  return components.length > 0
    ? components
    : [{ name: 'No components found', value: null, disabled: true }];
}

async function createBackup() {
  const { execSync } = require('child_process');

  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const branchName = `test-migration-backup-${timestamp}`;

    execSync(`git checkout -b ${branchName}`, { stdio: 'inherit' });
    execSync(`git add .`, { stdio: 'inherit' });
    execSync(`git commit -m "Pre-migration backup - ${timestamp}"`, { stdio: 'inherit' });

    console.log(chalk.green(`✅ Backup created on branch: ${branchName}`));
  } catch (error) {
    console.log(chalk.yellow('⚠️  Could not create git backup, proceeding without backup'));
  }
}

async function runTurboMigration(dryRun) {
  const { spawn } = require('child_process');

  const args = dryRun ? ['--dry-run'] : [];
  const turboProcess = spawn('node', ['scripts/turbo-migrate.js', ...args], {
    stdio: 'inherit',
    cwd: process.cwd(),
  });

  return new Promise((resolve, reject) => {
    turboProcess.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Turbo migration failed with code ${code}`));
      }
    });
  });
}

async function runSmartMigration(dryRun) {
  console.log(chalk.blue('🧠 Smart migration uses AI assistance. Please ensure you have:'));
  console.log('  - GitHub Copilot or similar AI assistant enabled');
  console.log('  - The migration prompts from .github/copilot-instructions.md loaded');

  const { spawn } = require('child_process');

  // For smart migration, we'll use the parallel migration tool with AI hints
  const args = ['--interactive', ...(dryRun ? ['--dry-run'] : [])];
  const smartProcess = spawn('node', ['scripts/migrate-by-type.js', ...args], {
    stdio: 'inherit',
    cwd: process.cwd(),
  });

  return new Promise((resolve, reject) => {
    smartProcess.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Smart migration failed with code ${code}`));
      }
    });
  });
}

async function runTargetedMigration(components, dryRun) {
  if (!components || components.length === 0) {
    console.log(chalk.yellow('⚠️  No components selected'));
    return;
  }

  console.log(chalk.blue(`🎯 Migrating ${components.length} components: ${components.join(', ')}`));

  const { spawn } = require('child_process');

  for (const component of components) {
    console.log(chalk.cyan(`\n▶️  Migrating ${component}...`));

    const args = [component, ...(dryRun ? ['--dry-run'] : [])];
    const migrateProcess = spawn('node', ['scripts/migrate-single.js', ...args], {
      stdio: 'inherit',
      cwd: process.cwd(),
    });

    await new Promise((resolve, reject) => {
      migrateProcess.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Migration failed for ${component}`));
        }
      });
    });
  }
}

async function runAnalysis() {
  const { spawn } = require('child_process');

  console.log(chalk.blue('📊 Running migration analysis...'));

  const analysisProcess = spawn('node', ['scripts/migration-dashboard.js'], {
    stdio: 'inherit',
    cwd: process.cwd(),
  });

  return new Promise((resolve, reject) => {
    analysisProcess.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error('Analysis failed'));
      }
    });
  });
}

// Handle errors gracefully
process.on('unhandledRejection', (error) => {
  console.error(chalk.red('❌ Migration failed:'), error.message);
  process.exit(1);
});

main().catch((error) => {
  console.error(chalk.red('❌ Migration failed:'), error.message);
  process.exit(1);
});
