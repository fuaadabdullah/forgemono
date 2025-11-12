import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { useEffect } from 'react';
import initializeSentry from '../src/services/sentry';
import { analytics, trackingEvents } from '../src/services/posthog';
import { QueryProvider } from '../src/providers/QueryProvider';

export default function RootLayout() {
  useEffect(() => {
    // Initialize crash reporting and analytics early in app lifecycle
    try { initializeSentry(); } catch {}
    analytics.init?.().catch(() => {});
    analytics.track?.(trackingEvents.APP_OPENED).catch(() => {});
    return () => {
      analytics.track?.(trackingEvents.APP_CLOSED).catch(() => {});
    };
  }, []);
  return (
    <QueryProvider>
      <SafeAreaProvider>
        <StatusBar style="dark" />
        <View style={{ flex: 1, backgroundColor: '#0b0f19' }}>
          <Stack screenOptions={{ headerShown: false }} />
        </View>
      </SafeAreaProvider>
    </QueryProvider>
  );
}
