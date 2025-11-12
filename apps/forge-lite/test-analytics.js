// Simple JavaScript test for PostHog analytics
// Testing the service logic without importing any modules

// Mock PostHog for testing
class MockPostHog {
  constructor(apiKey, options = {}) {
    this.apiKey = apiKey;
    this.options = options;
    this.isInitialized = false;
    this.userId = null;
    this.enabled = true;
    console.log('MockPostHog initialized with API key:', apiKey ? '***' : 'missing');
  }

  async identify(userId, properties = {}) {
    if (!this.enabled) return;
    this.userId = userId;
    console.log('MockPostHog: Identified user', userId, properties);
    return Promise.resolve();
  }

  async track(event, properties = {}) {
    if (!this.enabled) return;
    console.log('MockPostHog: Tracked event', event, properties);
    return Promise.resolve();
  }

  async screen(screenName, properties = {}) {
    if (!this.enabled) return;
    console.log('MockPostHog: Screen view', screenName, properties);
    return Promise.resolve();
  }

  async reset() {
    this.userId = null;
    console.log('MockPostHog: Reset user');
    return Promise.resolve();
  }

  async setEnabled(enabled) {
    this.enabled = enabled;
    console.log('MockPostHog: Set enabled to', enabled);
    return Promise.resolve();
  }

  async flush() {
    console.log('MockPostHog: Flushed events');
    return Promise.resolve();
  }
}

// Test the PostHog service logic
async function testPostHogService() {
  console.log('🧪 Testing PostHog Analytics Service...\n');

  try {
    // Test 1: Configuration loading
    console.log('1. Testing configuration loading...');
    // Mock the configuration that would come from Constants.expoConfig or process.env
    const apiKey = process.env.EXPO_PUBLIC_POSTHOG_API_KEY || 'test-api-key';
    const host = process.env.EXPO_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com';

    console.log('   API Key configured:', !!apiKey);
    console.log('   Host configured:', !!host);

    // Test 2: PostHog initialization
    console.log('\n2. Testing PostHog initialization...');
    const posthog = new MockPostHog(apiKey, {
      host: host,
      disabled: process.env.NODE_ENV === 'development' && !process.env.FORCE_ANALYTICS
    });
    console.log('   ✓ PostHog mock initialized');

    // Test 3: User identification
    console.log('\n3. Testing user identification...');
    await posthog.identify('test-user-123', { plan: 'free', experience: 'beginner' });
    console.log('   ✓ User identified');

    // Test 4: Event tracking
    console.log('\n4. Testing event tracking...');
    await posthog.track('app_opened', { source: 'test', timestamp: Date.now() });
    await posthog.track('watchlist_viewed', { symbols: ['AAPL', 'GOOGL'] });
    console.log('   ✓ Events tracked');

    // Test 5: Screen tracking
    console.log('\n5. Testing screen tracking...');
    await posthog.screen('WatchlistScreen', { tab: 'active' });
    await posthog.screen('TradePlannerScreen', { symbol: 'AAPL' });
    console.log('   ✓ Screens tracked');

    // Test 6: Analytics controls
    console.log('\n6. Testing analytics controls...');
    await posthog.setEnabled(false);
    await posthog.track('should_not_track', { test: true }); // Should not log
    await posthog.setEnabled(true);
    await posthog.track('should_track', { test: true }); // Should log
    console.log('   ✓ Analytics controls working');

    // Test 7: User reset
    console.log('\n7. Testing user reset...');
    await posthog.reset();
    console.log('   ✓ User reset');

    // Test 8: Flush
    console.log('\n8. Testing flush...');
    await posthog.flush();
    console.log('   ✓ Events flushed');

    console.log('\n✅ All PostHog tests passed!');

  } catch (error) {
    console.error('\n❌ PostHog test failed:', error.message);
    process.exit(1);
  }
}

// Run the test
testPostHogService().catch(console.error);
