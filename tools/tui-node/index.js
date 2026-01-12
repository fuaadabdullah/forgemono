#!/usr/bin/env node
'use strict';

const { loadConfig } = require('./lib/config');
const { selectCommand, validateCommand } = require('./lib/command-selector');
const { resolveWorkingDirectory } = require('./lib/path-resolver');
const { executeCommand } = require('./lib/command-runner');

async function run() {
  const argvConfigIndex = process.argv.indexOf('--config');
  const cfgPath = argvConfigIndex >= 0 ? process.argv[argvConfigIndex + 1] : undefined;
  const cfg = loadConfig(cfgPath);

  const commands = cfg.commands || {};
  if (Object.keys(commands).length === 0) {
    console.error(
      'No commands found in config. Copy tools/tui/config.json.example to tools/tui/config.json and edit.'
    );
    process.exit(1);
  }

  const key = await selectCommand(commands);
  if (!key) {
    console.log('No selection, exiting.');
    process.exit(0);
  }

  if (!validateCommand(key, commands)) {
    process.exit(3);
  }

  const cmd = commands[key];
  const cwd = resolveWorkingDirectory(cfg.cwd);

  try {
    await executeCommand(cmd, { cwd });
  } catch (err) {
    process.exit(err.exitCode || 1);
  }
}

run();
