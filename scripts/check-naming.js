const fs = require('fs');
const path = require('path');

const BAD_NAMES = [
  /^data$/,
  /^temp$/,
  /^tmp$/,
  /^foo$/,
  /^bar$/,
  /^baz$/,
  /^x$/,
  /^y$/,
  /^z$/,
  /^arr$/,
  /^obj$/,
  /^num$/,
  /^str$/,
  /^bool$/,
  /^func$/,
  /^fn$/,
  /^cb$/,
  /^e$/,
  /^err$/,
  /^res$/,
  /^req$/,
  /^param\d*$/,
  /^arg\d*$/,
];

// Naming pattern examples and suggestions
const NAMING_SUGGESTIONS = {
  // Boolean variables
  flag: 'isEnabled, hasPermission, shouldShow',
  status: 'isActive, isLoading, hasError',

  // Arrays and collections
  arr: 'users, items, products, results',
  list: 'userList, productList, itemList',

  // Generic objects
  obj: 'user, config, settings, metadata',
  data: 'userData, apiResponse, formData',

  // Functions and methods
  func: 'validateEmail, formatCurrency, processData',
  fn: 'calculateTotal, filterItems, transformData',

  // Event handlers
  e: 'event, clickEvent, inputEvent',

  // API related
  res: 'response, apiResponse, fetchResult',
  req: 'request, apiRequest, httpRequest',

  // Generic variables
  temp: 'temporaryValue, intermediateResult, buffer',
  tmp: 'temporaryData, intermediateValue',

  // Loop variables
  x: 'index, position, coordinateX',
  y: 'row, coordinateY',
  z: 'depth, coordinateZ',

  // Error handling
  err: 'error, apiError, validationError',

  // Numbers and strings
  num: 'count, total, amount, quantity',
  str: 'name, title, description, content',

  // Callbacks
  cb: 'onSuccess, onError, onComplete',

  // Parameters
  param: 'value, input, config',
  arg: 'argument, parameter, option',
};

// Context-based suggestions based on code patterns
function getContextualSuggestion(variableName, codeLine) {
  const line = codeLine.toLowerCase();

  // Boolean context
  if (
    line.includes('===') ||
    line.includes('!==') ||
    line.includes('true') ||
    line.includes('false') ||
    line.includes('&&') ||
    line.includes('||') ||
    line.includes('!')
  ) {
    return 'isLoading, hasPermission, shouldShow, isActive, canEdit';
  }

  // Array context
  if (
    line.includes('[') ||
    line.includes('push') ||
    line.includes('map') ||
    line.includes('filter') ||
    line.includes('forEach') ||
    line.includes('length')
  ) {
    return 'users, items, results, products, records';
  }

  // Event handler context
  if (
    line.includes('event') ||
    line.includes('onchange') ||
    line.includes('onclick') ||
    line.includes('onsubmit') ||
    line.includes('target')
  ) {
    return 'event, clickEvent, inputEvent, changeEvent';
  }

  // API/Fetch context
  if (
    line.includes('fetch') ||
    line.includes('api') ||
    line.includes('http') ||
    line.includes('response') ||
    line.includes('json')
  ) {
    return 'response, apiResponse, userData, result';
  }

  // Return general suggestions
  return NAMING_SUGGESTIONS[variableName] || 'descriptiveName, specificPurpose, clearIntent';
}

function checkFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const issues = [];

  lines.forEach((line, index) => {
    // Match variable declarations
    const varRegex = /(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)/g;
    let match;

    while ((match = varRegex.exec(line)) !== null) {
      const varName = match[1];

      // Check against bad names
      if (BAD_NAMES.some((pattern) => pattern.test(varName))) {
        issues.push({
          line: index + 1,
          variable: varName,
          code: line.trim(),
          suggestion: getContextualSuggestion(varName, line.trim()),
        });
      }
    }

    // Check function parameters
    const paramRegex = /function\s+\w+\s*\((.*?)\)|\((.*?)\)\s*=>/g;
    while ((match = paramRegex.exec(line)) !== null) {
      const params = (match[1] || match[2] || '').split(',').map((p) => p.trim());
      params.forEach((param) => {
        if (BAD_NAMES.some((pattern) => pattern.test(param))) {
          issues.push({
            line: index + 1,
            variable: param,
            code: line.trim(),
            type: 'parameter',
            suggestion: getContextualSuggestion(param, line.trim()),
          });
        }
      });
    }
  });

  return issues;
}

function runCheck() {
  // Check for common source directories in monorepo structure
  const possiblePaths = [
    path.join(__dirname, '../src'),
    path.join(__dirname, '../apps'),
    path.join(__dirname, '../packages'),
    path.join(__dirname, '../tools'),
    path.join(__dirname, '../GoblinOS'),
  ];

  let srcPath = null;
  for (const testPath of possiblePaths) {
    if (fs.existsSync(testPath)) {
      srcPath = testPath;
      break;
    }
  }

  if (!srcPath) {
    console.log('❌ No source directory found. Checked: src/, apps/, packages/, tools/, GoblinOS/');
    console.log(
      '💡 This script is designed for monorepo structures. Please ensure you have source code in one of the expected directories.'
    );
    process.exit(1);
  }

  console.log(`🔍 Checking naming conventions in: ${path.relative(process.cwd(), srcPath)}`);
  const files = getAllFiles(srcPath, ['.js', '.jsx', '.ts', '.tsx']);
  console.log(`📁 Found ${files.length} files to check`);

  const allIssues = [];
  files.forEach((file) => {
    const issues = checkFile(file);
    if (issues.length > 0) {
      allIssues.push({
        file: path.relative(process.cwd(), file),
        issues,
      });
    }
  });

  if (allIssues.length > 0) {
    console.log('\n🚨 Poorly named variables found:\n');
    console.log('💡 Naming Pattern Examples:');
    console.log('   Boolean: flag, status → isLoading, hasPermission (Clear boolean intent)');
    console.log('   Arrays:  arr, list → users, productList (Content-specific)');
    console.log('   Events:  e → event, clickEvent (Context + action)');
    console.log('   API:     res, req → response, apiRequest (Specific resource)');
    console.log('   Generic: data, temp → userData, temporaryValue (Descriptive purpose)\n');

    allIssues.forEach(({ file, issues }) => {
      console.log(`📄 ${file}:`);
      issues.forEach((issue) => {
        console.log(`  Line ${issue.line}: "${issue.variable}" in "${issue.code}"`);
        console.log(`    💡 Suggestion: ${issue.suggestion}`);
      });
      console.log();
    });

    console.log('🔧 Refactoring Example:');
    console.log('   // BEFORE - Vague names');
    console.log('   function proc(d) {');
    console.log('     let arr = [];');
    console.log('     for (let i = 0; i < d.length; i++) {');
    console.log('       if (d[i].s) arr.push(d[i]);');
    console.log('     }');
    console.log('     return arr;');
    console.log('   }');
    console.log('');
    console.log('   // AFTER - Descriptive names');
    console.log('   function filterActiveUsers(users: User[]): User[] {');
    console.log("     return users.filter(user => user.status === 'active');");
    console.log('   }\n');

    console.log(
      `📊 Summary: ${allIssues.length} files with issues, ${allIssues.reduce((sum, f) => sum + f.issues.length, 0)} total violations`
    );
    process.exit(1);
  } else {
    console.log(`✅ All variable names look good! (${files.length} files checked)`);
  }
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

runCheck();
