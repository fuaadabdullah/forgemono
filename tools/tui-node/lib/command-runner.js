let execa = require('execa');

// Normalize export shape across execa versions (CommonJS/ESM interop)
if (typeof execa !== 'function') {
  if (execa && typeof execa.default === 'function') {
    execa = execa.default;
  } else if (execa && typeof execa.execa === 'function') {
    execa = execa.execa;
  } else {
    throw new Error('Unsupported execa export shape; unable to run shell commands');
  }
}

/**
 * Execute a command using execa
 * @param {string} command - The command to execute
 * @param {object} options - Execution options
 * @param {string} options.cwd - Working directory
 * @returns {Promise<object>} Execution result
 */
async function executeCommand(command, options = {}) {
  const { cwd } = options;

  console.log(`Running: ${command}\nWorking dir: ${cwd}`);

  try {
    // Use execa(...) with shell:true for broad compatibility across execa versions
    const subprocess = execa(command, { shell: true, cwd });

    if (subprocess.stdout) subprocess.stdout.pipe(process.stdout);
    if (subprocess.stderr) subprocess.stderr.pipe(process.stderr);

    const result = await subprocess;
    // execa returns exitCode in `exitCode` or `code` depending on version; handle both
    const code = result.exitCode ?? result.code ?? 0;
    console.log(`\nCommand exited with code ${code}`);
    return result;
  } catch (err) {
    if (err.exitCode !== undefined) {
      console.error(`\nCommand failed with exit code ${err.exitCode}`);
    } else {
      console.error(`\nCommand error: ${err}`);
    }
    throw err;
  }
}

module.exports = { executeCommand };
