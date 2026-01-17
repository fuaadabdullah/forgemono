const prompts = require('prompts');

/**
 * Choose a command interactively using prompts
 * @param {object} commands - Available commands object
 * @returns {string|null} Selected command key or null if cancelled
 */
async function chooseCommand(commands) {
  const choices = Object.keys(commands).map((key) => ({ title: key, value: key }));
  const response = await prompts({
    type: 'select',
    name: 'cmd',
    message: 'Select a Goblin command',
    choices,
  });
  return response.cmd;
}

/**
 * Select a command based on environment variable or interactively
 * @param {object} commands - Available commands object
 * @returns {string|null} Selected command key or null if cancelled
 */
async function selectCommand(commands) {
  if (process.env.GOBLIN_CMD) {
    // Allow non-interactive selection for tests: name of command or numeric index (1-based)
    const g = process.env.GOBLIN_CMD;
    if (/^\d+$/.test(g)) {
      const idx = parseInt(g, 10) - 1;
      return Object.keys(commands)[idx];
    } else {
      return g;
    }
  } else {
    return await chooseCommand(commands);
  }
}

/**
 * Validate that the selected command exists
 * @param {string} commandKey - The command key to validate
 * @param {object} commands - Available commands object
 * @returns {boolean} True if command exists
 */
function validateCommand(commandKey, commands) {
  if (!commandKey || !commands[commandKey]) {
    console.error(`GOBLIN_CMD=${process.env.GOBLIN_CMD} did not match any command`);
    return false;
  }
  return true;
}

module.exports = { chooseCommand, selectCommand, validateCommand };
