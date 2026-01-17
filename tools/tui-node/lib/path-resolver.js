const path = require('path');

/**
 * Resolve working directory from template and configuration
 * @param {string} cwdTemplate - Template string for working directory
 * @returns {string} Resolved working directory path
 */
function resolveWorkingDirectory(cwdTemplate) {
  const template = cwdTemplate || '${repo_root}';
  let cwd = template;

  if (cwd && cwd.includes('${repo_root}')) {
    // Repo root default: two directories up from tools/tui-node
    const repoRoot = path.resolve(__dirname, '..', '..');
    cwd = cwd.replace('${repo_root}', repoRoot);
  }

  return cwd;
}

module.exports = { resolveWorkingDirectory };
