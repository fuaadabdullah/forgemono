// Ensure gesture handler is initialized before any navigation components.
import 'react-native-gesture-handler';

// Use the expo-router entrypoint so the router auto-discovers routes in /app
// The router provides its own root component; keep this file minimal.
import 'expo-router/entry';

// No exports required; `expo-router/entry` sets up the app entry for Expo and
// ensures Expo Router can discover `app/` routes (tabs, stacks, etc.).
