---
title: "Building RIZZK: What Worked, What Didn’t, and Why I Still Use It"
date: "2025-11-08"
description: "A candid look at building RIZZK, the mistakes, the wins, and why simple tools matter."
tags: ["case-study", "trading", "risk", "engineering", "indie-dev", "truth"]
image: "/assets/og/building-rizzk-case-study.png"
---

## Why Build a Risk Calculator?

I built RIZZK because I needed it myself. Most trading calculators are either too complicated, too salesy, or just plain unreliable. I wanted something I could trust—no hidden agenda, no upsells, just the math. RIZZK is what I wish I had when I started: a focused, offline-first calculator for sizing trades in R, not just dollars.

## What I Learned

- **Simplicity is hard:** I thought building a simple tool would be easy. It’s not. Every feature is a tradeoff between clarity and complexity. I cut a lot of ideas to keep RIZZK focused.
- **Type safety matters:** Using strict TypeScript and FastAPI for backend risk math meant fewer bugs and more confidence in results. But it also slowed me down at times.
- **Offline-first is a pain, but worth it:** Making things work without a network is harder than it looks. But it’s the only way I’d trust a tool like this.
- **No advice, just math:** I’m not a guru. RIZZK never gives signals or advice—just calculations. That’s a feature, not a bug.

## How I Built It

- **Frontend:** Expo (React Native) for cross-platform reach. It’s not perfect, but it gets the job done on iOS, Android, and web.
- **Backend:** FastAPI for all risk math, with unit tests. Python is fast to write, and easy to test.
- **Infra:** Supabase for user data, Fly.io for backend hosting. Both have free tiers, but you get what you pay for—expect some limits.
- **Testing:** Unit tests for every risk formula, E2E smoke tests. Bugs still slip through, but tests catch the big ones.

## Market Insights

- Most trading tools are bloated or locked behind paywalls. I’m not trying to compete with the big names. RIZZK is for people who want to understand their risk, not chase signals.
- Users value transparency—show the math, let them export their data. If you can’t see how it works, you shouldn’t trust it.

## What’s Next?

- More calculators (options, futures) if there’s demand
- Community templates, if people want to share
- Maybe open-sourcing the core logic—if it helps someone else

---

*Want more? Check out the [RIZZK Calculator](https://rizzk-calculator-demo-eus2-f1.azurewebsites.net/). If you have feedback, or want to build something together, let me know. I'm always learning, and I'd rather build with real users than guess what matters.*
