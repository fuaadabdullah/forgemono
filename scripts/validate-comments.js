// scripts/validate-comments.js
const fs = require('fs');
const path = require('path');

const EXCLUDED_FILES = ['test', 'spec', 'mock', '.d.ts', 'types/'];
const MIN_PUBLIC_FUNCTIONS_WITH_DOCS = 0.8; // 80% coverage

/**
 * Check if function has JSDoc comment
 */
function hasJsDocComment(content, functionStartIndex) {
  // Look back for comment
  const beforeFunction = content.substring(0, functionStartIndex);
  const lines = beforeFunction.split('\n').reverse();

  let foundComment = false;
  let inComment = false;

  for (let line of lines.slice(0, 30)) {
    const trimmed = line.trim();

    if (trimmed.startsWith('/**')) {
      foundComment = true;
      break;
    }

    // If we hit another function/export or non-comment, stop looking
    if (
      trimmed.includes('function') ||
      trimmed.includes('const') ||
      trimmed.includes('export') ||
      trimmed.includes('class') ||
      (trimmed !== '' && !trimmed.startsWith('//') && !trimmed.startsWith('/*'))
    ) {
      break;
    }
  }

  return foundComment;
}

/**
 * Extract JSDoc comment content
 */
function extractJSDocComment(content, functionStartIndex) {
  const beforeFunction = content.substring(0, functionStartIndex);
  const lines = beforeFunction.split('\n').reverse();

  let jsdocStart = -1;
  let jsdocEnd = -1;

  // Find JSDoc boundaries
  for (let i = 0; i < lines.length && i < 20; i++) {
    const line = lines[i].trim();
    if (line.startsWith('/**')) {
      jsdocStart = beforeFunction.split('\n').length - i;
      break;
    }
  }

  if (jsdocStart === -1) return null;

  // Find end of JSDoc
  for (let i = jsdocStart; i < content.split('\n').length; i++) {
    if (content.split('\n')[i].trim().endsWith('*/')) {
      jsdocEnd = i;
      break;
    }
  }

  if (jsdocEnd === -1) return null;

  return content
    .split('\n')
    .slice(jsdocStart, jsdocEnd + 1)
    .join('\n');
}

/**
 * Validate JSDoc content quality
 */
function validateJSDocQuality(jsdoc, functionName) {
  const issues = [];

  if (!jsdoc) {
    issues.push('Missing JSDoc comment');
    return issues;
  }

  // Check for required tags
  const hasReturns = jsdoc.includes('@returns') || jsdoc.includes('@return');
  if (!hasReturns) {
    issues.push('Missing @returns tag');
  }

  // Check for parameters (if function has params)
  const paramMatches = jsdoc.match(/@param\s+\w+/g);
  const functionSignature = jsdoc.split('\n').find((line) => line.includes(functionName));
  if (functionSignature) {
    // Simple heuristic: if function name is followed by parentheses with content, it likely has params
    const hasParams =
      functionSignature.includes('(') && functionSignature.split('(')[1].includes(',');
    if (hasParams && (!paramMatches || paramMatches.length === 0)) {
      issues.push('Missing @param tags for function parameters');
    }
  }

  // Check for example (recommended)
  if (!jsdoc.includes('@example')) {
    issues.push('Missing @example (recommended for exported functions)');
  }

  // Check for description
  const descriptionLines = jsdoc
    .split('\n')
    .filter(
      (line) =>
        line.trim().startsWith('*') &&
        !line.trim().startsWith('*/') &&
        !line.includes('@param') &&
        !line.includes('@returns') &&
        !line.includes('@return') &&
        !line.includes('@example') &&
        !line.includes('@throws') &&
        line.trim().length > 2
    );

  if (descriptionLines.length === 0) {
    issues.push('Missing description in JSDoc comment');
  }

  return issues;
}

/**
 * Analyze file for documentation issues
 */
function analyzeFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const issues = [];

  // Find exported functions without JSDoc
  const exportRegex = /export\s+(?:async\s+)?(?:function\s+(\w+)|const\s+(\w+)\s*=|class\s+(\w+))/g;
  let match;

  while ((match = exportRegex.exec(content)) !== null) {
    const functionName = match[1] || match[2] || match[3];
    const functionIndex = match.index;

    // Skip types and interfaces
    const line = content.substring(functionIndex, functionIndex + 200).split('\n')[0];
    if (line.includes('type') || line.includes('interface') || line.includes('export type')) {
      continue;
    }

    const hasJSDoc = hasJsDocComment(content, functionIndex);
    const jsdoc = hasJSDoc ? extractJSDocComment(content, functionIndex) : null;
    const qualityIssues = validateJSDocQuality(jsdoc, functionName);

    if (!hasJSDoc || qualityIssues.length > 0) {
      issues.push({
        name: functionName,
        line: content.substring(0, functionIndex).split('\n').length,
        hasJSDoc,
        qualityIssues,
      });
    }
  }

  return issues;
}

function getAllFiles(dirPath, extensions, arrayOfFiles = []) {
  let files;
  try {
    files = fs.readdirSync(dirPath);
  } catch (error) {
    // Skip directories we can't read (e.g., permission issues, broken symlinks)
    return arrayOfFiles;
  }

  files.forEach((file) => {
    const fullPath = path.join(dirPath, file);
    let stats;
    try {
      stats = fs.statSync(fullPath);
    } catch (error) {
      // Skip files we can't stat (e.g., broken symlinks)
      return;
    }

    if (stats.isDirectory()) {
      // Skip common directories that shouldn't be checked
      if (['node_modules', '.git', 'dist', 'build', '__pycache__', '.next'].includes(file)) {
        return;
      }
      arrayOfFiles = getAllFiles(fullPath, extensions, arrayOfFiles);
    } else if (extensions.some((ext) => file.endsWith(ext))) {
      arrayOfFiles.push(fullPath);
    }
  });

  return arrayOfFiles;
}

// Run validation
// Check for common source directories in monorepo structure
const possiblePaths = [
  path.join(__dirname, '../src'),
  path.join(__dirname, '../apps'),
  path.join(__dirname, '../packages'),
  path.join(__dirname, '../tools'),
  path.join(__dirname, '../GoblinOS'),
];

let srcPaths = [];
for (const testPath of possiblePaths) {
  if (fs.existsSync(testPath)) {
    srcPaths.push(testPath);
  }
}

if (srcPaths.length === 0) {
  console.log('❌ No source directories found. Checked: src/, apps/, packages/, tools/, GoblinOS/');
  console.log(
    '💡 This script is designed for monorepo structures. Please ensure you have source code in one of the expected directories.'
  );
  process.exit(1);
}

console.log(
  `🔍 Validating JSDoc comments in: ${srcPaths.map((p) => path.relative(process.cwd(), p)).join(', ')}`
);

let allFiles = [];
srcPaths.forEach((srcPath) => {
  allFiles = allFiles.concat(getAllFiles(srcPath, ['.ts', '.tsx', '.js', '.jsx']));
});

const srcFiles = allFiles;
let totalExports = 0;
let undocumentedExports = 0;
let qualityIssues = 0;

srcFiles.forEach((file) => {
  if (EXCLUDED_FILES.some((ex) => file.includes(ex))) return;

  const issues = analyzeFile(file);
  if (issues.length > 0) {
    console.log(`\n📄 ${path.relative(process.cwd(), file)}:`);
    issues.forEach((issue) => {
      totalExports++;
      if (!issue.hasJSDoc) {
        console.log(`  ❌ Line ${issue.line}: ${issue.name} - Missing JSDoc comment`);
        undocumentedExports++;
      } else {
        console.log(`  ⚠️  Line ${issue.line}: ${issue.name} - JSDoc quality issues:`);
        issue.qualityIssues.forEach((qi) => {
          console.log(`    • ${qi}`);
        });
        qualityIssues++;
      }
    });
  }
});

const documentedExports = totalExports - undocumentedExports;
const coverage = totalExports > 0 ? (documentedExports / totalExports) * 100 : 100;

console.log(`\n📊 Documentation Summary:`);
console.log(`  • Total exported functions: ${totalExports}`);
console.log(`  • Functions with JSDoc: ${documentedExports}`);
console.log(`  • Functions missing JSDoc: ${undocumentedExports}`);
console.log(`  • Functions with quality issues: ${qualityIssues}`);
console.log(`  • Coverage: ${coverage.toFixed(1)}%`);

if (undocumentedExports > 0 || coverage < MIN_PUBLIC_FUNCTIONS_WITH_DOCS * 100) {
  console.error(
    `\n❌ Below minimum ${MIN_PUBLIC_FUNCTIONS_WITH_DOCS * 100}% documentation coverage`
  );
  console.log('\n💡 JSDoc Guidelines:');
  console.log('  • All exported functions need JSDoc comments');
  console.log('  • Include description explaining what the function does');
  console.log('  • Use @param for each parameter with type and description');
  console.log('  • Use @returns to describe return value');
  console.log('  • Add @example showing typical usage');
  console.log('  • Use @throws for error conditions');
  process.exit(1);
}

if (qualityIssues > 0) {
  console.warn(`\n⚠️  ${qualityIssues} functions have JSDoc quality issues (see above)`);
  console.log('💡 Consider fixing these for better documentation quality');
}

console.log('\n✅ JSDoc validation passed!');
