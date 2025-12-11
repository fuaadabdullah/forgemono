# Lighthouse Audit Quick Reference Card

## 🎯 Your Mission
Audit 7 pages, record scores, document issues.

---

## 📋 Checklist

### Dashboard (`/`)

- [ ] Score: ___/100
- [ ] Passed: ___
- [ ] Issues: ________________________

### Chat (`/chat`)

- [ ] Score: ___/100
- [ ] Passed: ___
- [ ] Issues: ________________________

### Search (`/search`)

- [ ] Score: ___/100
- [ ] Passed: ___
- [ ] Issues: ________________________

### Settings (`/settings`)

- [ ] Score: ___/100
- [ ] Passed: ___
- [ ] Issues: ________________________

### Providers (`/providers`)

- [ ] Score: ___/100
- [ ] Passed: ___
- [ ] Issues: ________________________

### Logs (`/logs`)

- [ ] Score: ___/100
- [ ] Passed: ___
- [ ] Issues: ________________________

### Sandbox (`/sandbox`)

- [ ] Score: ___/100
- [ ] Passed: ___
- [ ] Issues: ________________________

---

## 🚀 Quick Start

1. **Open DevTools**: `Cmd+Option+I` (Mac) or `F12`
2. **Find Lighthouse Tab**: Look under `>>` if hidden
3. **Configure**: Check only "Accessibility", select "Desktop"
4. **Run**: Click "Analyze page load"
5. **Record**: Fill in checklist above
6. **Repeat**: Navigate to next page

---

## 📊 Score Interpretation

| Score | Meaning |
|-------|---------|
| 90-100 | ✅ Excellent - Ship it! |
| 75-89 | ⚠️ Good - Minor tweaks |
| 50-74 | 🟠 Needs work |
| 0-49 | ❌ Critical issues |

---

## 🐛 Common Issues We Might See

### Likely Issues (Quick Fixes)

- Missing `alt` attributes on decorative icons
- Button with icon but no accessible name
- Form input without associated label

### Unlikely Issues (We Have Good Coverage)

- ✅ Color contrast (16.64:1)
- ✅ Focus indicators (2px + glow)
- ✅ Skip link present
- ✅ Semantic HTML

---

## 📝 Recording Results

After all 7 audits:

1. Open: `scripts/summarize-lighthouse-results.js`
2. Fill in the `auditResults` object:

   ```javascript
   dashboard: {
     score: 95,
     passed: 48,
     warnings: ['Images missing alt text'],
     failed: []
   }
   ```
3. Run: `node scripts/summarize-lighthouse-results.js`
4. Review: `docs/ACCESSIBILITY_AUDIT_RESULTS.md`

---

## 💡 Tips

- **Save time**: Focus on Accessibility category only
- **Save reports**: Use "Save as HTML" for detailed records
- **Note patterns**: If same issue on multiple pages, note it once
- **Test realistic**: Use actual content, not loading states

---

## ⚠️ When to Stop & Ask for Help

- **Unexpected low scores** (<75 on any page)
- **Many failed audits** (>5 per page)
- **Unclear error messages**
- **Technical audit failures** (not content issues)

---

**Ready?** Open `http://localhost:3000` and let's go! 🚀
