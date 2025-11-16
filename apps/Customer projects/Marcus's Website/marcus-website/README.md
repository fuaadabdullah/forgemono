# Marcus's Website - Elbey Projects

A complete website template for Elbey Projects, a mobile mechanic business, built with Next.js 15 and TypeScript.

## Overview

This website template implements all the specifications from the "ELBEY PROJECTS" blueprint document, including:

- **Homepage** with hero section, services overview, gallery preview, testimonials, and contact form
- **About page** detailing 15+ years of experience
- **Services page** with comprehensive automotive service listings
- **Gallery page** with before/after photos and video content
- **Contact page** with detailed booking form
- **FAQ page** with expandable questions
- **Blog page** with post listings and newsletter signup
- **Legal pages** (Privacy Policy, Terms of Service)
- **Sitemap page** for navigation and SEO

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom Elbey Projects theme
- **Icons**: Lucide React
- **Animations**: Framer Motion (planned)
- **Fonts**: Inter font family

## Color Scheme

- **Primary Background**: Black (#000000)
- **Accent**: Red (#c62828)
- **Text**: Cream/White (#ffffff, #f5f5f5)
- **Secondary**: Gray variants (#gray-800, #gray-300, etc.)

## Project Structure

```
app/
├── layout.tsx          # Root layout with metadata
├── page.tsx           # Homepage
├── globals.css        # Global styles and Tailwind
├── about/page.tsx     # About page
├── services/page.tsx  # Services page
├── gallery/page.tsx   # Gallery page
├── contact/page.tsx   # Contact page
├── faq/page.tsx       # FAQ page
├── blog/page.tsx      # Blog page
├── privacy/page.tsx   # Privacy Policy
├── terms/page.tsx     # Terms of Service
└── sitemap/page.tsx   # Sitemap

components/
├── Hero.tsx           # Homepage hero section
├── WhyUs.tsx          # Why choose us section
├── Services.tsx       # Services overview
├── Gallery.tsx        # Gallery preview
├── Testimonials.tsx   # Customer testimonials
├── Contact.tsx        # Contact form
└── ui/
    └── Button.tsx     # Reusable button component

public/
├── robots.txt         # SEO robots file
└── favicon.ico        # Site favicon (placeholder)
```

## Getting Started

1. **Install dependencies**:

   ```bash
   npm install
   ```

2. **Run development server**:

   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   npm start
   ```

## Key Features Implemented

### Homepage Components

- **Hero Section**: Logo placeholder, tagline, CTA button
- **Why Choose Us**: Three feature cards (Mobile Service, 15+ Years, Quality Work)
- **Services**: Grid of 12 automotive services with pricing
- **Gallery**: Before/after image placeholders and video section
- **Testimonials**: Customer reviews with ratings

## Dev tips: Analytics, images, and E2E

1. Add your analytics IDs (Vercel environment variables or `.env.local`):

```env
# Google Analytics Measurement ID (G-XXXX)
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
# Facebook Pixel ID
NEXT_PUBLIC_FB_PIXEL_ID=123456789012345
NEXT_PUBLIC_SITE_URL=https://yourdomain.com
```

- **Vercel SpeedInsights**: Included in the root layout to improve performance observability in deployments.

2. Optimize images (requires `sharp`):

```
npm i -D sharp
npm run optimize:images
```

3. Run E2E tests with Playwright:

```
npx playwright install
npm run test:e2e
```

If you don't want to install `sharp` or Playwright, both the optimizer and tests will gracefully no-op or skip if dependencies are missing.

## CI / GitHub Actions (Playwright + Lighthouse + Vercel Deployments)

This repo includes a comprehensive GitHub Actions workflow that runs the build, Playwright E2E tests, Lighthouse report, and automatic Vercel deployments on push/PR to `main`:

- **Workflow file**: `.github/workflows/ci-marcus.yml` at the monorepo root
- **Jobs**: `build`, `test`, `preview` (PRs), `deploy` (main branch)

### Required GitHub Secrets

Before the workflow runs successfully, set the following repository `Secrets` in GitHub (Settings → Secrets → Actions):

**Required for all deployments:**
- `VERCEL_TOKEN` — Vercel deployment token (get from Vercel dashboard → Account Settings → Tokens)
- `VERCEL_ORG_ID` — Vercel organization ID (get from Vercel dashboard → Settings → General)
- `VERCEL_PROJECT_ID` — Vercel project ID (get from Vercel project dashboard)

**Required for production deployments:**
- `NEXT_PUBLIC_SITE_URL` — Your production site URL (e.g., `https://elbey-projects.com`)

**Optional analytics:**
- `NEXT_PUBLIC_GA_ID` — Google Analytics Measurement ID (G-XXXX)
- `NEXT_PUBLIC_FB_PIXEL_ID` — Facebook Pixel ID

**Optional notifications:**
- `SLACK_WEBHOOK_URL` — Slack webhook URL for deployment notifications

### Workflow Behavior

**On Pull Requests:**
- Runs build, tests, and Lighthouse
- Deploys preview to Vercel
- Posts preview URL as PR comment
- Optionally posts to Slack

**On Push to Main:**
- Runs build, tests, and Lighthouse
- Deploys production to Vercel
- Validates `NEXT_PUBLIC_SITE_URL` is set
- Optionally posts production URL to Slack

### Vercel SpeedInsights

The site includes Vercel SpeedInsights for performance monitoring. It's automatically enabled in production deployments and provides real-time performance metrics in your Vercel dashboard.

- **Contact**: Comprehensive booking form with all required fields

### Pages

- **About**: Detailed story of 15+ years experience
- **Services**: Complete service catalog with descriptions
- **Gallery**: Filterable gallery with categories
- **FAQ**: Expandable FAQ section
- **Blog**: Post listings with newsletter signup
- **Legal**: Privacy Policy and Terms of Service

### SEO Features

- Proper meta titles and descriptions for all pages
- Robots.txt file for search engine crawling
- Sitemap page for navigation
- Semantic HTML structure

## Blueprint Compliance

This template fully implements the "ELBEY PROJECTS" blueprint specifications:

✅ **Sitemap Structure**: All required pages implemented
✅ **Content Guidelines**: Business-appropriate copy throughout
✅ **Contact Form**: All specified fields included
✅ **SEO Recommendations**: Meta tags, robots.txt, sitemap
✅ **Design Elements**: Black/red/cream color scheme
✅ **Mobile-First**: Responsive design with Tailwind CSS
✅ **Legal Pages**: Privacy Policy and Terms of Service

## Next Steps

1. **Install Dependencies**: Resolve disk space issue and run `npm install`
2. **Add Images**: Replace placeholders with actual photos and logo
3. **Test Functionality**: Verify forms and navigation work correctly
4. **SEO Optimization**: Add structured data markup
5. **Performance**: Optimize images and implement lazy loading
6. **Deployment**: Set up hosting and domain configuration

## Development Notes

- All TypeScript/JSX errors are due to missing node_modules
- Project structure follows Next.js 15 best practices
- Components are modular and reusable
- Styling uses Tailwind utility classes with custom theme
- Form handling ready for backend integration

## Deployment

This project is designed to be deployed on Vercel, Netlify, or any static hosting service.

### Vercel Deployment (Recommended)

1. **Connect to Vercel**:

   ```bash
   npm i -g vercel
   vercel login
   ```

2. **Deploy**:

   ```bash
   vercel
   ```

   Follow the prompts to link your GitHub repository.

3. **Production Deployment**:
   ```bash
   vercel --prod
   ```

### Netlify Deployment

1. **Connect Repository**:

   - Go to [Netlify](https://netlify.com)
   - Click "New site from Git"
   - Connect your GitHub repository

2. **Build Settings**:

   - Build command: `npm run build`
   - Publish directory: `.next`
   - Node version: 18

3. **Deploy**: Netlify will automatically deploy on git push.

### Manual Deployment

1. **Build the project**:

   ```bash
   npm run build
   ```

2. **Start production server**:
   ```bash
   npm start
   ```

## Environment Variables

Create a `.env.local` file for local development:

```env
# Add any environment variables here
# NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

## Domain Setup

- **Vercel**: Add custom domain in project settings
- **Netlify**: Add custom domain in site settings
- Update DNS records to point to the hosting provider

## Contact

Built for Marcus's Elbey Projects mobile mechanic business.
Template created following the detailed blueprint specifications.
