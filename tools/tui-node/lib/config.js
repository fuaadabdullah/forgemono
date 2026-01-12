const fs = require('fs');
const path = require('path');

/**
 * Load configuration from a JSON file
 * @param {string} configPath - Path to the config file
 * @returns {object} Parsed configuration object
 */
function loadConfig(configPath) {
  const defaultPath = path.resolve(__dirname, '../../tui/config.json');
  const pth = configPath || defaultPath;

  try {
    const resolved = path.resolve(pth);
    const raw = fs.readFileSync(resolved, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    console.error(`Failed to load config ${pth}: ${err.message}`);
    process.exit(2);
  }
}

module.exports = { loadConfig };
