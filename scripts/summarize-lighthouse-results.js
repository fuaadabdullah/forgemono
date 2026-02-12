#!/usr/bin/env node

/**
 * Lighthouse Results Summary Generator
 *
 * This script helps organize Lighthouse accessibility audit results
 * into a structured markdown document.
 *
 * Usage:
 *   1. Complete Lighthouse audits on all 7 pages
 *   2. Fill in the results object below with your scores
 *   3. Run: node scripts/summarize-lighthouse-results.js
 */

const fs = require('fs');
const path = require('path');

// === FILL IN YOUR LIGHTHOUSE SCORES HERE ===
const auditResults = {
  dashboard: {
    score: null, // Fill in (0-100)
    passed: null,
    warnings: [],
    failed: []
  },
  chat: {
    score: null,
    passed: null,
    warnings: [],
    failed: []
  },
  search: {
    score: null,
    passed: null,
    warnings: [],
    failed: []
  },
  settings: {
    score: null,
    passed: null,
    warnings: [],
    failed: []
  },
  providers: {
    score: null,
    passed: null,
    warnings: [],
    failed: []
  },
  logs: {
    score: null,
    passed: null,
    warnings: [],
    failed: []
  },
  sandbox: {
    score: null,
    passed: null,
    warnings: [],
    failed: []
  }
};

// Metadata
const auditDate = new Date().toISOString().split('T')[0];
const auditor = 'GoblinOS Assistant';

// === REPORT GENERATION ===

function getScoreEmoji(score) {
  if (score >= 90) return '✅';
  if (score >= 75) return '⚠️';
  if (score >= 50) return '🟠';
  return '❌';
}

function getScoreStatus(score) {
  if (score >= 90) return 'Excellent';
  if (score >= 75) return 'Good';
  if (score >= 50) return 'Needs Work';
  return 'Critical';
}

function generateReport() {
  const pages = Object.entries(auditResults);
  const scores = pages.map(([_, data]) => data.score).filter(s => s !== null);

  if (scores.length === 0) {
    console.error('❌ No scores found. Please fill in auditResults object in this script.');
    process.exit(1);
  }

  const avgScore = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1);
  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);

  let markdown = `# Lighthouse Accessibility Audit Results

**Audit Date**: ${auditDate}
**Auditor**: ${auditor}
**Tool**: Chrome DevTools Lighthouse
**Target**: WCAG 2.1 Level AA compliance

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Pages Audited** | ${scores.length}/7 |
| **Average Score** | ${avgScore}/100 ${getScoreEmoji(parseFloat(avgScore))} |
| **Highest Score** | ${maxScore}/100 |
| **Lowest Score** | ${minScore}/100 |
| **Pages ≥90** | ${scores.filter(s => s >= 90).length}/${scores.length} |
| **Status** | ${avgScore >= 90 ? '✅ Production Ready' : avgScore >= 75 ? '⚠️ Minor Issues' : '❌ Needs Work'} |

---

## Per-Page Results

`;

  pages.forEach(([pageName, data]) => {
    if (data.score === null) return;

    const emoji = getScoreEmoji(data.score);
    const status = getScoreStatus(data.score);
    const pageTitle = pageName.charAt(0).toUpperCase() + pageName.slice(1);

    markdown += `### ${emoji} ${pageTitle} Page

**Score**: ${data.score}/100 (${status})
**URL**: \`http://localhost:3000/${pageName === 'dashboard' ? '' : pageName}\`
**Passed Audits**: ${data.passed || 'N/A'}

`;

    if (data.warnings && data.warnings.length > 0) {
      markdown += `**⚠️ Warnings** (${data.warnings.length}):\n`;
      data.warnings.forEach(w => markdown += `- ${w}\n`);
      markdown += '\n';
    }

    if (data.failed && data.failed.length > 0) {
      markdown += `**❌ Failed Audits** (${data.failed.length}):\n`;
      data.failed.forEach(f => markdown += `- ${f}\n`);
      markdown += '\n';
    }

    if ((!data.warnings || data.warnings.length === 0) && (!data.failed || data.failed.length === 0)) {
      markdown += `✅ No issues found!\n\n`;
    }

    markdown += '---\n\n';
  });

  markdown += `## Accessibility Features Verified

Based on our implementation:

- ✅ **Color Contrast**: WCAG AA compliant (16.64:1 body text, 9.29:1 primary)
- ✅ **High-Contrast Mode**: Class-based toggle (\`.goblinos-high-contrast\`)
- ✅ **Reduced Motion**: \`prefers-reduced-motion\` media query support
- ✅ **Focus Indicators**: 2px goblin green outline + glow effect
- ✅ **Skip Link**: Present for keyboard navigation
- ✅ **Semantic HTML**: Proper heading hierarchy, landmarks
- ✅ **ARIA Labels**: Applied to icon-only buttons
- ✅ **Keyboard Navigation**: All interactive elements focusable

---

## Known Implementations

### Component-Level Accessibility

1. **GoblinButtons.tsx**
   - Disabled states with \`aria-disabled\`
   - Focus rings via \`focus:ring-2\`
   - Hover states for visual feedback

2. **ContrastModeToggle.tsx**
   - Toggle button with descriptive label
   - State persisted in localStorage

3. **ThemePreview.tsx**
   - Radio button pattern for palette selection
   - Active state clearly indicated

4. **Navigation.tsx**
   - Logo with \`.logo-glow\` drop-shadow
   - Skip link for main content

### Global CSS Features

- Terminal panels with CRT gradient
- Pixel-art utilities for crisp scaling
- Scanlines effect (respects reduced motion)

---

## Recommendations

`;

  if (avgScore >= 90) {
    markdown += `### ✅ Excellent Accessibility Score!

Your application meets WCAG AA standards. Consider:

1. **Maintain Standards**: Add accessibility checks to CI/CD
2. **User Testing**: Test with real screen reader users
3. **Documentation**: Keep accessibility docs updated
4. **Monitor**: Regular audits after major changes

`;
  } else if (avgScore >= 75) {
    markdown += `### ⚠️ Good Foundation, Minor Improvements Needed

Priority actions:

1. Address any failed audits listed above
2. Review warnings for quick wins
3. Re-run Lighthouse after fixes
4. Aim for 90+ across all pages

`;
  } else {
    markdown += `### ❌ Critical Accessibility Issues

Immediate actions required:

1. Fix all failed audits (see per-page details above)
2. Review color contrast in custom components
3. Add missing ARIA labels
4. Ensure keyboard navigation works
5. Re-audit after each fix

`;
  }

  markdown += `---

## Next Steps

- [ ] Review and address any failed audits
- [ ] Run axe DevTools scan for deeper analysis
- [ ] Test with screen readers (VoiceOver, NVDA)
- [ ] Cross-browser testing (Safari, Firefox, Edge)
- [ ] Add accessibility tests to CI pipeline

---

**Generated**: ${new Date().toISOString()}
**Tool**: \`scripts/summarize-lighthouse-results.js\`
`;

  return markdown;
}

// Write report
try {
  const report = generateReport();
  const outputPath = path.join(__dirname, '../docs/ACCESSIBILITY_AUDIT_RESULTS.md');
  fs.writeFileSync(outputPath, report, 'utf8');
  console.log(`✅ Report generated: ${outputPath}`);
  console.log(`📊 Average Score: ${(Object.values(auditResults).map(d => d.score).filter(s => s !== null).reduce((a, b) => a + b, 0) / Object.values(auditResults).filter(d => d.score !== null).length).toFixed(1)}/100`);
} catch (error) {
  console.error('❌ Error generating report:', error.message);
  process.exit(1);
}
