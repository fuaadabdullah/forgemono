import fs from 'fs';
import path from 'path';

const pagesDir = path.join(process.cwd(), 'src', 'pages');
const servicesDir = path.join(process.cwd(), 'src', 'services');

const allowed = new Set([
  '_app.tsx',
  'index.tsx',
  'startup.tsx',
  'chat.tsx',
  'search.tsx',
  'sandbox.tsx',
  'account.tsx',
  'help.tsx',
  'onboarding.tsx',
  'login.tsx',
  'register.tsx',
  'google-callback.tsx',
  '404.tsx',
  path.join('admin', 'index.tsx'),
  path.join('admin', 'logs.tsx'),
  path.join('admin', 'providers.tsx'),
  path.join('admin', 'settings.tsx'),
]);

const ignoreFiles = new Set(['_document.tsx', '_error.tsx']);

const walk = (dir: string, base = ''): string[] => {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue;
    const rel = base ? path.join(base, entry.name) : entry.name;
    const full = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      files.push(...walk(full, rel));
      continue;
    }

    if (!/\.(tsx|ts)$/.test(entry.name)) continue;
    files.push(rel);
  }

  return files;
};

const found = walk(pagesDir).filter(file => !ignoreFiles.has(path.basename(file)));

const extras = found.filter(file => !allowed.has(file));
const missing = Array.from(allowed).filter(file => !found.includes(file));

if (extras.length || missing.length) {
  console.error('Routing check failed.');
  if (extras.length) {
    console.error('Unexpected route files:');
    extras.forEach(file => console.error(`- ${file}`));
  }
  if (missing.length) {
    console.error('Missing expected route files:');
    missing.forEach(file => console.error(`- ${file}`));
  }
  process.exit(1);
}

console.log('Routing check passed.');

/**
 * Routing constitution: services must not own frontend navigation.
 * Route strings like "/chat" belong in pages/screens/components, not in src/services/*.
 */
const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const forbiddenRouteLiterals = [
  '/chat',
  '/search',
  '/sandbox',
  '/account',
  '/help',
  '/login',
  '/register',
  '/startup',
  '/onboarding',
  '/admin',
] as const;

const forbiddenRoutePatterns: Array<{ route: string; pattern: RegExp }> = forbiddenRouteLiterals.map(
  route => {
    if (route === '/admin') {
      // Ban any admin path string ("/admin", "/admin/logs", etc.)
      return { route, pattern: new RegExp(String.raw`['"\`]${escapeRegExp(route)}`) };
    }

    // Ban exact frontend routes, allowing optional trailing "/" and optional query/hash.
    // Does not match API paths like "/chat/completions" or "/account/preferences".
    return {
      route,
      pattern: new RegExp(
        String.raw`['"\`]${escapeRegExp(route)}\/?(?:[?#'"\`]|$)`
      ),
    };
  }
);

const scriptExtensions = new Set(['.ts', '.tsx', '.js', '.jsx']);
const isScriptFile = (filePath: string) => scriptExtensions.has(path.extname(filePath));

const walkServiceFiles = (dir: string): string[] => {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkServiceFiles(full));
      continue;
    }
    if (!isScriptFile(full)) continue;
    files.push(full);
  }
  return files;
};

const serviceFiles = walkServiceFiles(servicesDir);
const violations: Array<{ file: string; route: string }> = [];

for (const file of serviceFiles) {
  const content = fs.readFileSync(file, 'utf8');
  for (const { route, pattern } of forbiddenRoutePatterns) {
    if (pattern.test(content)) {
      violations.push({ file, route });
    }
  }
}

if (violations.length > 0) {
  console.error('Routing check failed: forbidden frontend route strings detected in src/services.');
  violations
    .map(v => ({ ...v, rel: path.relative(process.cwd(), v.file) }))
    .sort((a, b) => a.rel.localeCompare(b.rel) || a.route.localeCompare(b.route))
    .forEach(v => console.error(`- ${v.rel}: contains "${v.route}"`));
  process.exit(1);
}

console.log('Service route-string check passed.');
