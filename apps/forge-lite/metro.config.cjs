const { getDefaultConfig } = require('@expo/metro-config');
const path = require('path');

// Start from Expo's default metro config for this project
const config = getDefaultConfig(__dirname);

// Map the deep import used by @expo/metro-runtime to our repo shim so it survives installs.
config.resolver = config.resolver || {};
config.resolver.extraNodeModules = Object.assign({}, config.resolver.extraNodeModules, {
  'react-native-web/dist/exports/NativeEventEmitter': path.resolve(__dirname, 'shims/NativeEventEmitter.js'),
  'missing-asset-registry-path': path.resolve(__dirname, 'shims/AssetRegistry.js'),
});

module.exports = config;
