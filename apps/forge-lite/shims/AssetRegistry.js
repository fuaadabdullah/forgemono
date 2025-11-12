// Minimal shim for missing-asset-registry-path used by @expo/metro-runtime
// This provides a fallback for asset resolution issues

const AssetRegistry = {
  registerAsset: () => {},
  getAssetByID: () => null,
  getAssetByName: () => null,
};

module.exports = AssetRegistry;
