#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { glob } = require('glob');

const MIGRATION_TEMPLATES = {
  // Common Enzyme → Testing Library patterns
  patterns: [
    {
      name: 'shallow-to-render',
      from: /const wrapper = shallow\(<([^>]+) \/>\)/g,
      to: 'const { container } = render(<$1 />)',
    },
    {
      name: 'find-to-getByRole',
      from: /wrapper\.find\(['"]([^'"]+)['"]\)/g,
      to: (match, selector) => {
        // Map common selectors to roles
        const roleMap = {
          button: 'button',
          input: 'textbox',
          form: 'form',
          a: 'link',
          select: 'combobox',
        };
        const role = roleMap[selector] || 'generic';
        return `screen.getByRole('${role}')`;
      },
    },
    {
      name: 'simulate-to-userEvent',
      from: /\.simulate\(['"]([^'"]+)['"]/g,
      to: (match, event) => {
        const eventMap = {
          click: 'click',
          change: 'type',
          submit: 'submit',
          focus: 'focus',
          blur: 'blur',
        };
        const userEvent = eventMap[event] || event;
        return `await userEvent.${userEvent}(`;
      },
    },
    {
      name: 'enzyme-import-to-testing-library',
      from: /import\s+{\s*shallow,\s*mount\s*}\s+from\s+['"]enzyme['"]/g,
      to: "import { render, screen } from '@testing-library/react';\nimport userEvent from '@testing-library/user-event'",
    },
    {
      name: 'wrapper-exists-to-screen-queries',
      from: /expect\(wrapper\.exists?\(\)\)\.toBe\(true\)/g,
      to: "expect(screen.getByRole('generic')).toBeInTheDocument()",
    },
    {
      name: 'wrapper-text-to-screen-text',
      from: /expect\(wrapper\.text\(\)\)\.toBe\(['"]([^'"]+)['"]\)/g,
      to: "expect(screen.getByText('$1')).toBeInTheDocument()",
    },
  ],
};

function findTestFiles(basePath = './src') {
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

  scanDirectory(basePath);
  return testFiles;
}

function turboMigrateFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf-8');
  let changes = [];
  let hasEnzymeImport = false;

  // Check if file uses Enzyme
  if (content.includes("from 'enzyme'") || content.includes('from "enzyme"')) {
    hasEnzymeImport = true;
  }

  if (!hasEnzymeImport) {
    return false; // Skip files that don't use Enzyme
  }

  // Apply each pattern
  MIGRATION_TEMPLATES.patterns.forEach((pattern) => {
    const newContent = content.replace(pattern.from, pattern.to);
    if (newContent !== content) {
      changes.push(pattern.name);
      content = newContent;
    }
  });

  // Add userEvent setup if userEvent is used
  if (content.includes('userEvent.') && !content.includes('userEvent.setup()')) {
    // Find the test block and add userEvent setup
    const testBlockRegex = /(describe|test|it)\(['"]([^'"]+)['"],\s*\(.*?async\s*\(\)\s*=>\s*{/gs;
    content = content.replace(testBlockRegex, (match) => {
      if (!match.includes('userEvent.setup()')) {
        return match.replace(
          /async\s*\(\)\s*=>\s*{/,
          'async () => {\n  const user = userEvent.setup();'
        );
      }
      return match;
    });
  }

  if (changes.length > 0) {
    fs.writeFileSync(filePath, content);
    console.log(`⚡ ${path.relative(process.cwd(), filePath)}: Applied ${changes.join(', ')}`);
    return true;
  }

  return false;
}

function generateReport(migratedFiles, totalFiles, outputPath = './migration-report.json') {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalFiles: totalFiles,
      migratedFiles: migratedFiles.length,
      skippedFiles: totalFiles - migratedFiles.length,
    },
    migratedFiles: migratedFiles.map((file) => path.relative(process.cwd(), file)),
    recommendations: [
      'Review migrated files manually for complex patterns',
      'Run tests to ensure functionality is preserved',
      'Consider adding @testing-library/jest-dom for additional matchers',
      'Update test documentation to reflect Testing Library patterns',
    ],
  };

  fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
  console.log(`📊 Migration report saved to ${outputPath}`);
}

// Main execution
async function main() {
  const args = process.argv.slice(2);
  const basePath = args[0] || './src';

  console.log('🔍 Finding test files...');
  const testFiles = findTestFiles(basePath);
  console.log(`📁 Found ${testFiles.length} test files`);

  if (testFiles.length === 0) {
    console.log("❌ No test files found. Make sure you're in the right directory.");
    process.exit(1);
  }

  console.log('🚀 Starting turbo migration...');
  let migrated = [];
  let processed = 0;

  for (const file of testFiles) {
    process.stdout.write(`\rProcessing: ${processed + 1}/${testFiles.length}`);
    if (turboMigrateFile(file)) {
      migrated.push(file);
    }
    processed++;
  }

  console.log(`\n\n✅ Migration complete!`);
  console.log(`📈 Migrated ${migrated.length}/${testFiles.length} files automatically`);

  if (migrated.length > 0) {
    generateReport(migrated, testFiles.length);
  }

  if (migrated.length < testFiles.length) {
    console.log('\n💡 Tip: Files without Enzyme usage were skipped.');
    console.log('   Manual review recommended for complex migration patterns.');
  }
}

// Handle glob import dynamically
async function run() {
  try {
    // Try to use glob if available, fallback to fs-based search
    let glob;
    try {
      glob = (await import('glob')).default;
    } catch (e) {
      // glob not available, will use fs-based search
    }

    if (glob) {
      // Revert to glob-based search if available
      global.findTestFiles = function (basePath = './src') {
        const patterns = [
          '**/*.test.{js,jsx,ts,tsx}',
          '**/*.spec.{js,jsx,ts,tsx}',
          '**/__tests__/**/*.{js,jsx,ts,tsx}',
        ];

        let allFiles = [];
        patterns.forEach((pattern) => {
          const files = glob.sync(pattern, {
            cwd: basePath,
            absolute: true,
          });
          allFiles = allFiles.concat(files);
        });

        return [...new Set(allFiles)];
      };
    }

    await main();
  } catch (error) {
    console.error('❌ Migration failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  run();
}

module.exports = { turboMigrateFile, findTestFiles, MIGRATION_TEMPLATES };
