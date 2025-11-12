---
description: "README"
---

# ForgeTM Lite

A free, cross-platform trading cockpit for retail traders and students.

## Overview

**ForgeTM Lite** is an educational trading application that helps traders learn proper risk management and position sizing. Built with Expo (React Native) for iOS, Android, and Web platforms.

### Core Features
- ✅ **Watchlist + Pre-trade Planning** - Research and plan trades
- ✅ **Risk Sizing Calculator** - Calculate position sizes based on risk percentage
- ✅ **Trading Journal** - Track trades and performance analytics
- ❌ **NO Broker Execution** - Educational only, not a trading platform
- ❌ **NO Trading Signals** - Focus on discipline and risk management

### Philosophy
- **Truth over vibes** - Everything measured in R first, dollars second
- **Offline-first** - Works on the train, syncs when online
- **Free forever core** - Monetize edges, not essentials

## Tech Stack

### Frontend
- **Framework**: Expo (React Native) - iOS, Android, Web
- **Language**: TypeScript (strict mode)
- **Navigation**: Expo Router
- **State**: React hooks + Context

### Backend
- **API**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL + Row Level Security)
- **Auth**: Supabase Auth
- **Market Data**: Alpha Vantage API (server-side only)

### Infrastructure
- **Hosting**: Fly.io (API), Supabase (Database)
- **Build**: EAS (Expo Application Services)
- **Telemetry**: Sentry (crashes), PostHog (analytics)

## Development

### Prerequisites
- Node.js 18+
- Python 3.9+
- Expo CLI
- EAS CLI

### Setup
```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Run on specific platform
pnpm ios      # iOS Simulator
pnpm android  # Android Emulator
pnpm web      # Web browser
```

### Testing
```bash
# Unit tests
pnpm test

# Smoke tests
pnpm test:smoke

# E2E tests
pnpm test:e2e
```

### Building
```bash
# Development build
pnpm build:dev

# Production build
pnpm build:production

# Submit to app stores
pnpm submit:ios
pnpm submit:android
```

## API Documentation

### Risk Calculation Endpoints

#### POST /api/risk/calculate
Calculate position size based on risk parameters.

**Request:**
```json
{
  "entry_price": 150.00,
  "stop_loss": 145.00,
  "equity": 10000.00,
  "risk_percent": 1.0
}
```

**Response:**
```json
{
  "position_size": 690,
  "risk_amount": 100.00,
  "r_multiple": 2.5
}
```

### Market Data Endpoints

#### GET /api/market/quote/{ticker}
Get current market quote for a ticker.

**Response:**
```json
{
  "ticker": "AAPL",
  "price": 150.25,
  "change": 2.50,
  "change_percent": 1.69,
  "volume": 52847392,
  "last_updated": "2024-01-15T16:00:00Z"
}
```

## GoblinOS Automation

This project uses GoblinOS for development automation. Available commands:

```bash
# Development
pnpm goblin:dev     # Start development environment

# Testing
pnpm goblin:test    # Run full test suite

# Release
pnpm goblin:build   # Build for all platforms
pnpm goblin:submit  # Submit to app stores
```

## Project Structure

```
apps/forge-lite/
├── src/
│   ├── app/                 # Expo Router screens
│   ├── components/          # Reusable UI components
│   ├── services/            # API clients
│   ├── utils/               # Utilities
│   └── types/               # TypeScript types
├── api/                     # FastAPI backend
│   ├── main.py             # FastAPI app
│   ├── routers/            # API endpoints
│   └── services/           # Business logic
├── supabase/               # Database migrations
├── assets/                 # Images and fonts
└── scripts/                # Automation scripts
```

## Compliance & Privacy

### Educational Only
This application is for educational purposes only. It does not provide financial advice, trading recommendations, or broker services.

### Data Export
Users can export their data at any time for GDPR compliance.

### Privacy Policy
- No personal trading data is shared with third parties
- Market data is fetched server-side only
- Crash reports and analytics are anonymized

## Contributing

1. Follow the existing code style (TypeScript strict mode)
2. Add tests for new features
3. Update documentation
4. Ensure offline-first functionality

## License

MIT License - Free for educational and personal use.

## Version

v1.0.0

---
*Generated automatically on 2025-11-07T14:13:42.553Z*
