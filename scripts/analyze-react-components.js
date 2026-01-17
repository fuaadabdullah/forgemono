#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class ComponentAnalyzer {
  constructor(options = {}) {
    this.options = {
      srcPath: options.srcPath || './src',
      output: options.output || './complexity-report.json',
      format: options.format || 'json',
      ...options,
    };

    this.stats = {
      totalComponents: 0,
      byComplexity: {
        simple: 0,
        medium: 0,
        complex: 0,
        monster: 0,
      },
      analysis: [],
    };
  }

  findComponents() {
    const components = [];

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

            // Match React component files
            if (
              (ext === '.js' || ext === '.jsx' || ext === '.ts' || ext === '.tsx') &&
              !item.endsWith('.test.js') &&
              !item.endsWith('.test.jsx') &&
              !item.endsWith('.test.ts') &&
              !item.endsWith('.test.tsx') &&
              !item.endsWith('.spec.js') &&
              !item.endsWith('.spec.jsx') &&
              !item.endsWith('.spec.ts') &&
              !item.endsWith('.spec.tsx')
            ) {
              // Quick check if it's a React component
              const content = fs.readFileSync(fullPath, 'utf-8');
              if (this.isReactComponent(content)) {
                components.push(fullPath);
              }
            }
          }
        }
      } catch (error) {
        // Skip directories we can't read
      }
    }

    scanDirectory(this.options.srcPath);
    return components;
  }

  isReactComponent(content) {
    // Check for React component patterns
    return (
      (content.includes('function ') && content.includes('return') && content.includes('<')) ||
      (content.includes('const ') &&
        content.includes('= (') &&
        content.includes('=>') &&
        content.includes('<')) ||
      (content.includes('class ') && content.includes('extends React.Component')) ||
      (content.includes('export default') && content.includes('<')) ||
      (content.includes('export function') && content.includes('return') && content.includes('<'))
    );
  }

  analyzeComponent(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const lines = content.split('\n');

      const analysis = {
        path: filePath,
        relativePath: path.relative(process.cwd(), filePath),
        name: this.extractComponentName(content, filePath),
        lines: lines.length,
        complexity: 'simple',
        factors: {
          propsCount: 0,
          stateVariables: 0,
          hooks: [],
          effects: 0,
          contexts: 0,
          apiCalls: 0,
          eventHandlers: 0,
          conditionalRendering: 0,
          children: false,
          styled: false,
          typescript: path.extname(filePath).includes('ts'),
        },
        migrationDifficulty: 'easy',
        estimatedTime: '5min',
      };

      // Analyze props
      const propsMatch = content.match(/interface\s+\w+Props|type\s+\w+Props/g);
      if (propsMatch) {
        const propsContent = this.extractPropsInterface(content);
        analysis.factors.propsCount = this.countProps(propsContent);
      }

      // Count state variables
      analysis.factors.stateVariables = (content.match(/useState\(/g) || []).length;

      // Count hooks
      const hookMatches = content.match(/use\w+\(/g) || [];
      analysis.factors.hooks = [...new Set(hookMatches.map((h) => h.replace('(', '')))];

      // Count effects
      analysis.factors.effects = (content.match(/useEffect\(/g) || []).length;

      // Count contexts
      analysis.factors.contexts = (content.match(/useContext\(/g) || []).length;

      // Count API calls (fetch, axios, etc.)
      analysis.factors.apiCalls = (content.match(/(fetch|axios\.|\.get\(|\.post\()/g) || []).length;

      // Count event handlers
      analysis.factors.eventHandlers = (content.match(/on\w+=/g) || []).length;

      // Count conditional rendering
      analysis.factors.conditionalRendering =
        (content.match(/{\s*\w+\s*\?/g) || []).length +
        (content.match(/&&/g) || []).filter((match) =>
          content.substring(content.indexOf(match) - 10, content.indexOf(match) + 10).includes('<')
        ).length;

      // Check for children
      analysis.factors.children = content.includes('children') || content.includes('Children');

      // Check for styled components
      analysis.factors.styled =
        content.includes('styled.') ||
        content.includes('styled(') ||
        content.includes('css`') ||
        content.includes('styled-components');

      // Determine complexity
      analysis.complexity = this.calculateComplexity(analysis);
      analysis.migrationDifficulty = this.calculateMigrationDifficulty(analysis);
      analysis.estimatedTime = this.estimateMigrationTime(analysis);

      return analysis;
    } catch (error) {
      return {
        path: filePath,
        relativePath: path.relative(process.cwd(), filePath),
        error: error.message,
        complexity: 'unknown',
      };
    }
  }

  extractComponentName(content, filePath) {
    // Try to extract component name from export default
    const exportMatch = content.match(/export\s+default\s+(?:function\s+)?(\w+)/);
    if (exportMatch) return exportMatch[1];

    // Try to extract from function declaration
    const funcMatch = content.match(/function\s+(\w+)\s*\(/);
    if (funcMatch) return funcMatch[1];

    // Try to extract from const declaration
    const constMatch = content.match(/const\s+(\w+)\s*=\s*\(/);
    if (constMatch) return constMatch[1];

    // Fallback to filename
    return path.basename(filePath, path.extname(filePath));
  }

  extractPropsInterface(content) {
    const interfaceMatch = content.match(/interface\s+\w+Props\s*{([^}]*)}/);
    if (interfaceMatch) return interfaceMatch[1];

    const typeMatch = content.match(/type\s+\w+Props\s*=\s*{([^}]*)}/);
    if (typeMatch) return typeMatch[1];

    return '';
  }

  countProps(propsContent) {
    if (!propsContent) return 0;
    return (propsContent.match(/;/g) || []).length;
  }

  calculateComplexity(analysis) {
    const factors = analysis.factors;
    let score = 0;

    // Size factors
    if (analysis.lines > 500) score += 3;
    else if (analysis.lines > 200) score += 2;
    else if (analysis.lines > 100) score += 1;

    // Complexity factors
    score += factors.stateVariables * 0.5;
    score += factors.effects * 1;
    score += factors.contexts * 1;
    score += factors.apiCalls * 1.5;
    score += factors.eventHandlers * 0.3;
    score += factors.conditionalRendering * 0.5;
    score += factors.propsCount * 0.1;

    if (factors.children) score += 0.5;
    if (factors.styled) score += 1;
    if (factors.typescript) score += 0.5;

    if (score >= 5) return 'monster';
    if (score >= 3) return 'complex';
    if (score >= 1.5) return 'medium';
    return 'simple';
  }

  calculateMigrationDifficulty(analysis) {
    const complexity = analysis.complexity;
    const factors = analysis.factors;

    if (complexity === 'monster') return 'hard';
    if (complexity === 'complex') return 'medium';
    if (factors.apiCalls > 0 || factors.effects > 2) return 'medium';
    return 'easy';
  }

  estimateMigrationTime(analysis) {
    const baseTimes = {
      simple: 5,
      medium: 15,
      complex: 30,
      monster: 60,
    };

    let time = baseTimes[analysis.complexity] || 30;

    // Adjust for factors
    if (analysis.factors.apiCalls > 0) time += 10;
    if (analysis.factors.effects > 2) time += 15;
    if (analysis.factors.contexts > 1) time += 10;

    return `${time}min`;
  }

  generateReport() {
    const components = this.findComponents();
    console.log(`🔍 Analyzing ${components.length} React components...\n`);

    for (const component of components) {
      const analysis = this.analyzeComponent(component);
      this.stats.analysis.push(analysis);
      this.stats.byComplexity[analysis.complexity]++;
      this.stats.totalComponents++;
    }

    // Sort by complexity (monster first)
    const complexityOrder = { monster: 4, complex: 3, medium: 2, simple: 1 };
    this.stats.analysis.sort(
      (a, b) => complexityOrder[b.complexity] - complexityOrder[a.complexity]
    );

    return {
      timestamp: new Date().toISOString(),
      summary: {
        totalComponents: this.stats.totalComponents,
        byComplexity: this.stats.byComplexity,
        migrationTimeEstimate: this.estimateTotalMigrationTime(),
      },
      components: this.stats.analysis,
    };
  }

  estimateTotalMigrationTime() {
    const timeMultipliers = {
      simple: 5,
      medium: 15,
      complex: 30,
      monster: 60,
    };

    let totalMinutes = 0;
    for (const component of this.stats.analysis) {
      const timeStr = component.estimatedTime.replace('min', '');
      totalMinutes += parseInt(timeStr);
    }

    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  }

  displayReport(report) {
    console.log('📊 COMPONENT COMPLEXITY ANALYSIS\n');
    console.log('═'.repeat(80));

    console.log(`\n📈 SUMMARY`);
    console.log(`   Total components: ${report.summary.totalComponents}`);
    console.log(`   Estimated migration time: ${report.summary.migrationTimeEstimate}`);
    console.log('');

    console.log('🎯 COMPLEXITY BREAKDOWN');
    for (const [complexity, count] of Object.entries(report.summary.byComplexity)) {
      if (count > 0) {
        const percentage = ((count / report.summary.totalComponents) * 100).toFixed(1);
        console.log(`   ${complexity.toUpperCase()}: ${count} components (${percentage}%)`);
      }
    }

    console.log('\n🏆 TOP 10 MOST COMPLEX COMPONENTS\n');

    report.components.slice(0, 10).forEach((comp, index) => {
      console.log(`${index + 1}. ${comp.name}`);
      console.log(`   📁 ${comp.relativePath}`);
      console.log(`   📊 ${comp.complexity.toUpperCase()} (${comp.lines} lines)`);
      console.log(`   ⏱️  Est. migration: ${comp.estimatedTime}`);
      console.log(`   🔧 Difficulty: ${comp.migrationDifficulty}`);
      console.log(`   📋 Factors: ${this.formatFactors(comp.factors)}`);
      console.log('');
    });

    console.log('═'.repeat(80));
  }

  formatFactors(factors) {
    const parts = [];
    if (factors.propsCount > 0) parts.push(`${factors.propsCount} props`);
    if (factors.stateVariables > 0) parts.push(`${factors.stateVariables} state vars`);
    if (factors.hooks.length > 0) parts.push(`${factors.hooks.length} hooks`);
    if (factors.effects > 0) parts.push(`${factors.effects} effects`);
    if (factors.apiCalls > 0) parts.push(`${factors.apiCalls} API calls`);
    if (factors.contexts > 0) parts.push(`${factors.contexts} contexts`);
    if (factors.children) parts.push('children');
    if (factors.styled) parts.push('styled');

    return parts.join(', ') || 'none';
  }

  saveReport(report) {
    if (this.options.format === 'json') {
      fs.writeFileSync(this.options.output, JSON.stringify(report, null, 2));
      console.log(`💾 JSON report saved to ${this.options.output}`);
    } else if (this.options.format === 'csv') {
      this.saveCsvReport(report);
    }
  }

  saveCsvReport(report) {
    const csvPath = this.options.output.replace('.json', '.csv');
    const csvHeader =
      'Name,Path,Complexity,Lines,Props,StateVars,Hooks,Effects,APICalls,Contexts,MigrationDifficulty,EstimatedTime\n';

    const csvRows = report.components.map((comp) => {
      const f = comp.factors || {};
      return [
        comp.name,
        comp.relativePath,
        comp.complexity,
        comp.lines,
        f.propsCount || 0,
        f.stateVariables || 0,
        f.hooks?.length || 0,
        f.effects || 0,
        f.apiCalls || 0,
        f.contexts || 0,
        comp.migrationDifficulty,
        comp.estimatedTime.replace('min', ''),
      ].join(',');
    });

    fs.writeFileSync(csvPath, csvHeader + csvRows.join('\n'));
    console.log(`💾 CSV report saved to ${csvPath}`);
  }

  async run() {
    const report = this.generateReport();
    this.displayReport(report);
    this.saveReport(report);
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
      case '--output':
      case '-o':
        options.output = args[++i];
        break;
      case '--format':
      case '-f':
        options.format = args[++i];
        break;
      case '--help':
      case '-h':
        console.log(`
React Component Complexity Analyzer

Usage: node scripts/analyze-react-components.js [options]

Options:
  -s, --src <path>         Source path (default: ./src)
  -o, --output <file>      Output file (default: ./complexity-report.json)
  -f, --format <format>    Output format: json or csv (default: json)
  -h, --help               Show this help

Examples:
  node scripts/analyze-react-components.js
  node scripts/analyze-react-components.js --format csv --output components.csv
        `);
        process.exit(0);
    }
  }

  const analyzer = new ComponentAnalyzer(options);
  await analyzer.run();
}

if (require.main === module) {
  main().catch((error) => {
    console.error('❌ Analysis failed:', error.message);
    process.exit(1);
  });
}

module.exports = ComponentAnalyzer;
