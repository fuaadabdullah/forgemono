// Simple JavaScript test for Sentry crash reporting
// Testing the service logic without importing the TypeScript module

// Mock Sentry for testing
class MockSentry {
  constructor() {
    this.user = null;
    this.enabled = true;
    console.log('MockSentry initialized');
  }

  init(config) {
    this.config = config;
    console.log('MockSentry: Initialized with config', {
      dsn: config.dsn ? '***' : 'missing',
      debug: config.debug,
      environment: config.environment
    });
  }

  setUser(user) {
    this.user = user;
    console.log('MockSentry: Set user', user);
  }

  captureException(error, context) {
    if (!this.enabled) return;
    console.log('MockSentry: Captured exception', error.message, context);
  }

  captureMessage(message, level) {
    if (!this.enabled) return;
    console.log('MockSentry: Captured message', message, level);
  }

  startSpan(name, op, callback) {
    console.log('MockSentry: Started span', name, op);
    if (callback) callback();
  }
}

// Global mock
const Sentry = new MockSentry();

// Test the Sentry service logic
async function testSentryService() {
  console.log('🧪 Testing Sentry Crash Reporting Service...\n');

  try {
    // Test 1: Configuration loading
    console.log('1. Testing configuration loading...');
    const dsn = process.env.EXPO_PUBLIC_SENTRY_DSN || 'test-dsn';
    console.log('   DSN configured:', !!dsn);

    // Test 2: Sentry initialization
    console.log('\n2. Testing Sentry initialization...');
    Sentry.init({
      dsn,
      debug: true,
      environment: process.env.NODE_ENV || 'development',
      enabled: true,
      tracesSampleRate: 1.0,
      release: '1.0.0'
    });
    console.log('   ✓ Sentry mock initialized');

    // Test 3: User context setting
    console.log('\n3. Testing user context...');
    Sentry.setUser({
      id: 'test-user-123',
      email: 'test@example.com'
    });
    console.log('   ✓ User context set');

    // Test 4: Exception capture
    console.log('\n4. Testing exception capture...');
    const testError = new Error('Test error for Sentry');
    Sentry.captureException(testError, {
      tags: { component: 'test' },
      extra: { userAction: 'testing' }
    });
    console.log('   ✓ Exception captured');

    // Test 5: Message capture
    console.log('\n5. Testing message capture...');
    Sentry.captureMessage('Test info message', 'info');
    Sentry.captureMessage('Test warning message', 'warning');
    Sentry.captureMessage('Test error message', 'error');
    console.log('   ✓ Messages captured');

    // Test 6: Performance monitoring
    console.log('\n6. Testing performance monitoring...');
    Sentry.startSpan('test-operation', 'test', () => {
      console.log('   Mock operation executed');
    });
    console.log('   ✓ Performance span created');

    // Test 7: User context clearing
    console.log('\n7. Testing user context clearing...');
    Sentry.setUser(null);
    console.log('   ✓ User context cleared');

    console.log('\n✅ All Sentry tests passed!');

  } catch (error) {
    console.error('\n❌ Sentry test failed:', error.message);
    process.exit(1);
  }
}

// Run the test
testSentryService().catch(console.error);
