# Lighthouse Accessibility Audit Guide

## Prerequisites

- ✅ Dev server running at `<http://localhost:3000`>
- ✅ Chrome or Chromium-based browser (Edge, Brave, etc.)

## Step-by-Step Instructions

### 1. Open Chrome DevTools

1. Navigate to `<http://localhost:3000`>
2. Press `F12` or `Cmd+Option+I` (macOS) / `Ctrl+Shift+I` (Windows/Linux)
3. Click on the **Lighthouse** tab (may be hidden under `>>` overflow menu)

### 2. Configure Lighthouse Settings

1. **Categories**: Check only **Accessibility** (uncheck Performance, Best Practices, SEO, PWA)
2. **Device**: Select **Desktop** (or Mobile for responsive testing)
3. **Throttling**: Select **Desktop** or **No throttling** for local dev
4. Click **Analyze page load** button

### 3. Pages to Audit (7 Total)

Run Lighthouse on each of these URLs:

| # | Page | URL | Expected Components |
|---|------|-----|---------------------|
| 1 | **Dashboard** | `<http://localhost:3000/`> | Logo glow, hero section, stats cards |
| 2 | **Chat** | `<http://localhost:3000/chat`> | Message bubbles, input field, send button |
| 3 | **Search** | `<http://localhost:3000/search`> | Search input, filters, results |
| 4 | **Settings** | `<http://localhost:3000/settings`> | Theme preview, provider cards, toggles |
| 5 | **Providers** | `<http://localhost:3000/providers`> | Config cards, API key status |
| 6 | **Logs** | `<http://localhost:3000/logs`> | Terminal output, filters |
| 7 | **Sandbox** | `<http://localhost:3000/sandbox`> | Interactive demos, code editor |

### 4. Record Results

For each page, capture:

- **Score** (0-100, target ≥90)
- **Passed Audits** count
- **Warnings** (if any)
- **Failed Audits** (if any)
  - Audit name
  - Element(s) affected
  - Suggested fix

### 5. Export Reports (Optional)

After each audit:

1. Click the **⚙️ gear icon** → **Save as HTML**
2. Save to: `/Users/fuaadabdullah/ForgeMonorepo/docs/lighthouse-reports/`
3. Naming convention: `lighthouse-[page]-[date].html`
   - Example: `lighthouse-dashboard-2025-12-02.html`

## What Lighthouse Checks

### Accessibility Audits Include:

- ✅ Color contrast ratios (WCAG AA)
- ✅ ARIA attributes validity
- ✅ Button/link names
- ✅ Image alt text
- ✅ Form labels
- ✅ Heading hierarchy
- ✅ Keyboard navigation
- ✅ Focus indicators
- ✅ Language declaration
- ✅ Document title
- ✅ Skip links
- ✅ Valid HTML

## Target Scores

| Score Range | Status | Action |
|-------------|--------|--------|
| 90-100 | ✅ Excellent | No action needed |
| 75-89 | ⚠️ Good | Review warnings, optional fixes |
| 50-74 | ⚠️ Needs Work | Fix major issues |
| 0-49 | ❌ Poor | Critical fixes required |

## Common Issues & Quick Fixes

### Issue: Low Contrast
**Fix**: Already handled by our token system (16.64:1 body text)

- Verify `--text` on `--bg` combinations
- Check custom component overrides

### Issue: Missing ARIA Labels
**Fix**: Add to interactive elements without visible text

```tsx
<button aria-label="Open menu">
  <MenuIcon />
</button>
```

### Issue: Form Inputs Without Labels
**Fix**: Associate labels with inputs
```tsx

<label htmlFor="email">Email</label>
<input id="email" type="email" />
```

### Issue: Images Without Alt Text
**Fix**: Add descriptive alt attributes

```tsx
<img src="logo.png" alt="Goblin Assistant logo" />
```

### Issue: Poor Heading Hierarchy
**Fix**: Use proper H1→H2→H3 nesting
```tsx

<h1>Page Title</h1>
<section>
  <h2>Section Title</h2>
  <h3>Subsection</h3>
</section>
```

## After Completing All 7 Audits

Run this command to generate summary:

```bash
cd /Users/fuaadabdullah/ForgeMonorepo
node scripts/summarize-lighthouse-results.js
```

This will create: `docs/ACCESSIBILITY_AUDIT_RESULTS.md`

## Next Steps

1. **If all pages score ≥90**: Proceed to axe DevTools scan
2. **If any page scores <90**: Review failed audits and apply fixes
3. **If Critical issues found**: Create GitHub issues and prioritize

---

**Need Help?**
- Check existing accessibility implementations in `docs/ACCESSIBILITY_SUMMARY.md`
- Review WCAG guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Ask me to help interpret Lighthouse findings!
