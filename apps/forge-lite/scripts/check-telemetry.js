#!/usr/bin/env node

/**
 * Telemetry check script for ForgeTM Lite
 * Verifies Sentry and PostHog configuration
 */

const fs = require('fs');
const path = require('path');

const projectRoot = path.join(__dirname, '..');
const envPath = path.join(projectRoot, '.env.local');

function checkTelemetryConfig() {
  console.log('🔍 Checking telemetry configuration...\n');

  // Check if .env.local exists
  if (!fs.existsSync(envPath)) {
    console.log('❌ .env.local file not found');
    console.log('📝 Create .env.local with the following variables:');
    console.log('   SENTRY_DSN=your_sentry_dsn_here');
    console.log('   POSTHOG_API_KEY=your_posthog_key_here');
    console.log('   POSTHOG_HOST=your_posthog_host_here\n');
    return false;
  }

  // Read environment variables
  const envContent = fs.readFileSync(envPath, 'utf8');
  const envVars = {};

  envContent.split('\n').forEach(line => {
    const [key, value] = line.split('=');
    if (key && value) {
      envVars[key.trim()] = value.trim();
    }
  });

  let allGood = true;

  // Check Sentry configuration
  if (!envVars.EXPO_PUBLIC_SENTRY_DSN) {
    console.log('❌ EXPO_PUBLIC_SENTRY_DSN not configured');
    allGood = false;
  } else {
    console.log('✅ EXPO_PUBLIC_SENTRY_DSN configured');
  }

  // Check PostHog configuration
  if (!envVars.EXPO_PUBLIC_POSTHOG_API_KEY) {
    console.log('❌ EXPO_PUBLIC_POSTHOG_API_KEY not configured');
    allGood = false;
  } else {
    console.log('✅ EXPO_PUBLIC_POSTHOG_API_KEY configured');
  }

  if (!envVars.EXPO_PUBLIC_POSTHOG_HOST) {
    console.log('❌ EXPO_PUBLIC_POSTHOG_HOST not configured');
    allGood = false;
  } else {
    console.log('✅ EXPO_PUBLIC_POSTHOG_HOST configured');
  }

  // Check if telemetry is integrated in the app
  const appJsonPath = path.join(projectRoot, 'app.json');
  if (fs.existsSync(appJsonPath)) {
    const appJson = JSON.parse(fs.readFileSync(appJsonPath, 'utf8'));
    const hasSentry = appJson.expo?.plugins?.some(plugin =>
      Array.isArray(plugin) && plugin[0] === '@sentry/react-native/expo'
    );

    if (hasSentry) {
      console.log('✅ Sentry plugin configured in app.json');
    } else {
      console.log('⚠️  Sentry plugin not found in app.json');
      console.log('   Add to app.json expo.plugins:');
      console.log('   ["@sentry/react-native/expo", { "url": "https://sentry.io/" }]');
    }
  }

  console.log('');

  if (allGood) {
    console.log('🎉 Telemetry configuration is complete!');
    return true;
  } else {
    console.log('❌ Telemetry configuration incomplete');
    console.log('📖 See docs/telemetry-setup.md for setup instructions');
    return false;
  }
}

function checkPackageDependencies() {
  console.log('🔍 Checking telemetry dependencies...\n');

  const packageJsonPath = path.join(projectRoot, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    console.log('❌ package.json not found');
    return false;
  }

  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };

  const requiredDeps = [
    '@sentry/react-native',
    'posthog-react-native'
  ];

  let allDepsPresent = true;

  requiredDeps.forEach(dep => {
    if (deps[dep]) {
      console.log(`✅ ${dep} installed (${deps[dep]})`);
    } else {
      console.log(`❌ ${dep} not installed`);
      allDepsPresent = false;
    }
  });

  if (!allDepsPresent) {
    console.log('\n📦 Install missing dependencies:');
    console.log('   pnpm add @sentry/react-native sentry-expo posthog-react-native');
  }

  console.log('');
  return allDepsPresent;
}

// Main execution
try {
  const configGood = checkTelemetryConfig();
  const depsGood = checkPackageDependencies();

  if (configGood && depsGood) {
    console.log('🎉 Telemetry setup is ready!');
    process.exit(0);
  } else {
    console.log('❌ Telemetry setup needs attention');
    process.exit(1);
  }
} catch (error) {
  console.error('❌ Error checking telemetry:', error);
  process.exit(1);
}
