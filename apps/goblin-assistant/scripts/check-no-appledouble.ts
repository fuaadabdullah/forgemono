import fs from 'fs';
import path from 'path';

const projectRoot = process.cwd();
const srcRoot = path.join(projectRoot, 'src');

const IGNORE_DIRS = new Set(['node_modules', '.next', 'dist', 'coverage']);

const walk = (dir: string): string[] => {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    if (entry.name.startsWith('.') && entry.name !== '.DS_Store' && !entry.name.startsWith('._')) {
      // Skip hidden folders like .git, but still allow checks for AppleDouble
      continue;
    }

    const full = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      if (IGNORE_DIRS.has(entry.name)) continue;
      files.push(...walk(full));
      continue;
    }

    files.push(full);
  }

  return files;
};

if (!fs.existsSync(srcRoot)) {
  console.log('No src/ directory found, skipping AppleDouble check.');
  process.exit(0);
}

const allFiles = walk(srcRoot);
const offenders = allFiles.filter(file => {
  const base = path.basename(file);
  return base.startsWith('._') || base === '.DS_Store';
});

if (offenders.length > 0) {
  console.error('AppleDouble / OS metadata files detected (delete them; they break builds):');
  offenders
    .map(file => path.relative(projectRoot, file))
    .sort()
    .forEach(file => console.error(`- ${file}`));
  process.exit(1);
}

console.log('AppleDouble check passed.');

