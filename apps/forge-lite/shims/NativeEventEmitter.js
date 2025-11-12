// Minimal web shim for NativeEventEmitter to satisfy imports used by Expo/metro runtime.
// Placed in repo so it survives node_modules reinstalls and can be aliased by Metro.
class NativeEventEmitter {
  addListener() {
    return { remove: () => {} };
  }
  removeListener() {}
  removeAllListeners() {}
  emit() {}
}

// CommonJS export for Metro resolver compatibility
module.exports = NativeEventEmitter;

// ESM default export
exports.default = NativeEventEmitter;
