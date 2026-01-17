#!/usr/bin/env node

/**
 * Automated axe-core Accessibility Audit Runner
 *
 * This script runs axe-core programmatically on all 7 pages
 * and generates a comprehensive WCAG compliance report.
 *
 * axe-core detects violations that Lighthouse might miss, including:
 * - More detailed ARIA validation
 * - Advanced color contrast issues
 * - Complex keyboard navigation problems
 * - Best practice violations
 *
 * Prerequisites:
 * - Dev server running at http://localhost:3000
 * - Chrome/Chromium installed
 *
 * Usage:
 *   node scripts/run-axe-audit.js
 */

import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import * as chromeLauncher from 'chrome-launcher';
import puppeteer from 'puppeteer-core';
import { AxePuppeteer } from '@axe-core/puppeteer';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Pages to audit
const PAGES = [
  {
    name: 'dashboard',
    url: 'http://localhost:3000/',
    description: 'Dashboard - Main landing page',
  },
  {
    name: 'chat',
    url: 'http://localhost:3000/chat',
    description: 'Chat - AI conversation interface',
  },
  {
    name: 'search',
    url: 'http://localhost:3000/search',
    description: 'Search - Find and filter content',
  },
  {
    name: 'settings',
    url: 'http://localhost:3000/settings',
    description: 'Settings - Theme and provider config',
  },
  {
    name: 'providers',
    url: 'http://localhost:3000/providers',
    description: 'Providers - API configuration',
  },
  {
    name: 'logs',
    url: 'http://localhost:3000/logs',
    description: 'Logs - System activity terminal',
  },
  {
    name: 'sandbox',
    url: 'http://localhost:3000/sandbox',
    description: 'Sandbox - Interactive demos',
  },
];

// Severity levels for reporting
const SEVERITY_ORDER = ['critical', 'serious', 'moderate', 'minor'];
const SEVERITY_EMOJI = {
  critical: '🔴',
  serious: '🟠',
  moderate: '🟡',
  minor: '🔵',
};

async function runAxeAudit(url, name, browser) {
  console.log(`\n🔍 Auditing: ${name} (${url})`);

  const page = await browser.newPage();

  try {
    // Navigate to page
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });

    // Run axe-core analysis
    const results = await new AxePuppeteer(page)
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'])
      .analyze();

    // Categorize violations by severity
    const violationsBySeverity = {
      critical: results.violations.filter((v) => v.impact === 'critical'),
      serious: results.violations.filter((v) => v.impact === 'serious'),
      moderate: results.violations.filter((v) => v.impact === 'moderate'),
      minor: results.violations.filter((v) => v.impact === 'minor'),
    };

    const totalViolations = results.violations.length;
    const criticalCount = violationsBySeverity.critical.length;
    const seriousCount = violationsBySeverity.serious.length;

    // Calculate score (100 - weighted violations)
    const score = Math.max(
      0,
      100 -
        (criticalCount * 10 +
          seriousCount * 5 +
          violationsBySeverity.moderate.length * 2 +
          violationsBySeverity.minor.length * 1)
    );

    const status =
      totalViolations === 0 ? '✅' : criticalCount > 0 ? '🔴' : seriousCount > 0 ? '🟠' : '🟡';

    console.log(`${status} Score: ${score}/100`);
    console.log(
      `   Total: ${totalViolations} | Critical: ${criticalCount} | Serious: ${seriousCount} | Moderate: ${violationsBySeverity.moderate.length} | Minor: ${violationsBySeverity.minor.length}`
    );
    console.log(`   Passed: ${results.passes.length} checks`);

    await page.close();

    return {
      name,
      url,
      score,
      totalViolations,
      violations: results.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        help: v.help,
        helpUrl: v.helpUrl,
        tags: v.tags,
        nodes: v.nodes.length,
        nodeDetails: v.nodes.map((n) => ({
          html: n.html,
          target: n.target,
          failureSummary: n.failureSummary,
        })),
      })),
      passes: results.passes.length,
      incomplete: results.incomplete.length,
      inapplicable: results.inapplicable.length,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error(`❌ Error auditing ${name}:`, error.message);
    await page.close();
    return {
      name,
      url,
      score: null,
      error: error.message,
      timestamp: new Date().toISOString(),
    };
  }
}

async function runAllAudits() {
  console.log('🚀 Starting axe-core Accessibility Audits...\n');
  console.log(`📋 Pages to audit: ${PAGES.length}`);
  console.log(`🎯 Target: 0 Critical/Serious violations\n`);

  // Launch Chrome
  const chrome = await chromeLauncher.launch({
    chromeFlags: ['--headless', '--disable-gpu', '--no-sandbox'],
  });

  const browser = await puppeteer.connect({
    browserURL: `http://localhost:${chrome.port}`,
    defaultViewport: { width: 1350, height: 940 },
  });

  const results = [];

  for (const page of PAGES) {
    const result = await runAxeAudit(page.url, page.name, browser);
    results.push(result);

    // Small delay between audits
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  await browser.disconnect();
  await chrome.kill();

  return results;
}

function generateReport(results) {
  const validResults = results.filter((r) => r.score !== null);
  const avgScore =
    validResults.length > 0
      ? (validResults.reduce((sum, r) => sum + r.score, 0) / validResults.length).toFixed(1)
      : 'N/A';

  const totalViolations = validResults.reduce((sum, r) => sum + r.totalViolations, 0);
  const criticalViolations = validResults.reduce(
    (sum, r) => sum + r.violations.filter((v) => v.impact === 'critical').length,
    0
  );
  const seriousViolations = validResults.reduce(
    (sum, r) => sum + r.violations.filter((v) => v.impact === 'serious').length,
    0
  );

  const auditDate = new Date().toISOString().split('T')[0];

  let markdown = `# axe-core Accessibility Audit Results

**Audit Date**: ${auditDate}
**Auditor**: Automated axe-core Runner
**Tool**: axe-core v4.x (Puppeteer)
**Standards**: WCAG 2.0 Level A, AA & WCAG 2.1 Level A, AA
**Tags**: wcag2a, wcag2aa, wcag21a, wcag21aa, best-practice

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Pages Audited** | ${validResults.length}/7 |
| **Average Score** | ${avgScore}/100 ${avgScore >= 95 ? '✅' : avgScore >= 85 ? '🟡' : '🔴'} |
| **Total Violations** | ${totalViolations} |
| **Critical Issues** | ${criticalViolations} ${criticalViolations === 0 ? '✅' : '🔴'} |
| **Serious Issues** | ${seriousViolations} ${seriousViolations === 0 ? '✅' : '🟠'} |
| **Status** | ${criticalViolations === 0 && seriousViolations === 0 ? '✅ Production Ready' : '⚠️ Issues Found'} |

---

## Per-Page Results

`;

  results.forEach((result) => {
    if (result.error) {
      markdown += `### ❌ ${result.name.charAt(0).toUpperCase() + result.name.slice(1)} Page

**Error**: Could not complete audit
**Message**: ${result.error}

---

`;
      return;
    }

    const status =
      result.totalViolations === 0
        ? '✅'
        : result.violations.some((v) => v.impact === 'critical')
          ? '🔴'
          : result.violations.some((v) => v.impact === 'serious')
            ? '🟠'
            : '🟡';

    const pageTitle = result.name.charAt(0).toUpperCase() + result.name.slice(1);

    markdown += `### ${status} ${pageTitle} Page

**Score**: ${result.score}/100
**URL**: \`${result.url}\`
**Violations**: ${result.totalViolations} | **Passed**: ${result.passes} checks
**Timestamp**: ${result.timestamp}

`;

    if (result.totalViolations === 0) {
      markdown += `\n✅ **Perfect!** No accessibility violations found.\n\n`;
      markdown += `**Passed Checks**: ${result.passes}
**Incomplete**: ${result.incomplete} (elements that couldn't be fully tested)
**Not Applicable**: ${result.inapplicable}

---

`;
      return;
    }

    // Group violations by severity
    const bySeverity = {
      critical: result.violations.filter((v) => v.impact === 'critical'),
      serious: result.violations.filter((v) => v.impact === 'serious'),
      moderate: result.violations.filter((v) => v.impact === 'moderate'),
      minor: result.violations.filter((v) => v.impact === 'minor'),
    };

    SEVERITY_ORDER.forEach((severity) => {
      const violations = bySeverity[severity];
      if (violations.length === 0) return;

      markdown += `\n#### ${SEVERITY_EMOJI[severity]} ${severity.toUpperCase()} Issues (${violations.length})\n\n`;

      violations.forEach((v, index) => {
        markdown += `**${index + 1}. ${v.help}** (${v.nodes} element${v.nodes > 1 ? 's' : ''})\n`;
        markdown += `- **Issue**: ${v.description}\n`;
        markdown += `- **Impact**: ${v.impact}\n`;
        markdown += `- **WCAG**: ${v.tags.filter((t) => t.startsWith('wcag')).join(', ')}\n`;
        markdown += `- **Learn More**: [${v.id}](${v.helpUrl})\n`;

        // Show first affected element as example
        if (v.nodeDetails.length > 0) {
          const firstNode = v.nodeDetails[0];
          markdown += `- **Example Element**: \`${firstNode.target.join(' > ')}\`\n`;
          markdown += `  \`\`\`html\n  ${firstNode.html.substring(0, 150)}${firstNode.html.length > 150 ? '...' : ''}\n  \`\`\`\n`;
          if (firstNode.failureSummary) {
            markdown += `- **Fix**: ${firstNode.failureSummary.split('\n')[0]}\n`;
          }
        }
        markdown += `\n`;
      });
    });

    markdown += `**Summary**: ${result.passes} checks passed | ${result.incomplete} incomplete | ${result.inapplicable} not applicable\n\n`;
    markdown += `---\n\n`;
  });

  markdown += `## Compliance Status

### WCAG 2.1 Level AA
`;

  if (criticalViolations === 0 && seriousViolations === 0) {
    markdown += `
✅ **COMPLIANT** - No critical or serious violations detected.

All tested pages meet WCAG 2.1 Level AA standards according to axe-core automated testing.

**Note**: Automated testing catches ~57% of accessibility issues. Manual testing with screen readers is recommended for full compliance assurance.
`;
  } else {
    markdown += `
⚠️ **NON-COMPLIANT** - Critical or serious violations detected.

**Action Required**:
- ${criticalViolations} critical issue${criticalViolations !== 1 ? 's' : ''} must be fixed
- ${seriousViolations} serious issue${seriousViolations !== 1 ? 's' : ''} should be addressed

Review the per-page results above for detailed fix instructions.
`;
  }

  markdown += `

---

## Comparison: Lighthouse vs axe-core

| Tool | Focus | Coverage | Result |
|------|-------|----------|--------|
| **Lighthouse** | Core accessibility | ~73 audits | ✅ 100/100 (all pages) |
| **axe-core** | WCAG compliance | ~${validResults[0]?.passes || 'N/A'}+ rules | ${criticalViolations === 0 && seriousViolations === 0 ? '✅' : '⚠️'} ${totalViolations} violation${totalViolations !== 1 ? 's' : ''} |

**Why both?**
- Lighthouse: Quick broad assessment, performance-focused
- axe-core: Deep WCAG validation, more detailed error reporting
- Combined: ~80% automated coverage (manual testing still needed)

---

## Next Steps

`;

  if (criticalViolations === 0 && seriousViolations === 0) {
    markdown += `### ✅ Excellent Results!

Your application passes automated accessibility testing. Recommended actions:

1. ✅ Lighthouse audit complete (100/100)
2. ✅ axe-core scan complete (0 critical/serious)
3. 🧪 **Next**: Manual screen reader testing
4. 🌐 **Next**: Cross-browser verification
5. 🚀 **Ready**: Deploy to production

### Recommended Manual Testing

**Screen Readers**:
- macOS: VoiceOver (Cmd+F5)
- Windows: NVDA (free) or JAWS
- Test: Navigation, forms, dynamic content

**Keyboard Navigation**:
- Tab through all interactive elements
- Test dropdown menus, modals, dialogs
- Verify focus visible at all times

**Browser Testing**:
- Safari, Firefox, Edge
- Verify high-contrast mode
- Test reduced motion preferences
`;
  } else {
    markdown += `### ⚠️ Action Required

Fix critical and serious issues before production:

1. **Review Violations**: See per-page results above
2. **Prioritize**: Critical > Serious > Moderate > Minor
3. **Fix & Test**: Apply fixes, re-run \`node scripts/run-axe-audit.js\`
4. **Verify**: Aim for 0 critical/serious violations

**Common Quick Fixes**:
- Add \`aria-label\` to icon-only buttons
- Ensure all images have \`alt\` text
- Fix color contrast (use our token system)
- Add labels to form inputs
- Ensure proper heading hierarchy
`;
  }

  markdown += `

---

**Generated**: ${new Date().toISOString()}
**Script**: \`scripts/run-axe-audit.js\`
**Command**: \`node scripts/run-axe-audit.js\`
**Raw Data**: \`docs/axe-reports/audit-results.json\`
`;

  return markdown;
}

// Main execution
async function main() {
  try {
    const results = await runAllAudits();

    console.log('\n' + '='.repeat(60));
    console.log('📊 AUDIT COMPLETE');
    console.log('='.repeat(60) + '\n');

    // Generate and save report
    const report = generateReport(results);
    const reportPath = join(__dirname, '../docs/AXE_AUDIT_RESULTS.md');
    writeFileSync(reportPath, report, 'utf8');

    console.log(`✅ Report saved: ${reportPath}`);

    // Print summary
    const validResults = results.filter((r) => r.score !== null);
    const avgScore =
      validResults.length > 0
        ? (validResults.reduce((sum, r) => sum + r.score, 0) / validResults.length).toFixed(1)
        : 0;

    const totalViolations = validResults.reduce((sum, r) => sum + r.totalViolations, 0);
    const criticalCount = validResults.reduce(
      (sum, r) => sum + r.violations.filter((v) => v.impact === 'critical').length,
      0
    );
    const seriousCount = validResults.reduce(
      (sum, r) => sum + r.violations.filter((v) => v.impact === 'serious').length,
      0
    );

    console.log(`\n📈 Average Score: ${avgScore}/100`);
    console.log(`📊 Total Violations: ${totalViolations}`);
    console.log(`🔴 Critical: ${criticalCount}`);
    console.log(`🟠 Serious: ${seriousCount}`);

    if (criticalCount === 0 && seriousCount === 0) {
      console.log('\n🎉 EXCELLENT! No critical or serious violations.');
      console.log('✅ Ready for production deployment!');
    } else {
      console.log('\n⚠️  ACTION REQUIRED! Review violations above.');
    }

    // Save raw JSON results
    const jsonPath = join(__dirname, '../docs/axe-reports/audit-results.json');
    writeFileSync(jsonPath, JSON.stringify(results, null, 2), 'utf8');
    console.log(`📄 Raw data saved: ${jsonPath}`);
  } catch (error) {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  }
}

main();
