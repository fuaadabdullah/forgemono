import fs from 'fs';
import path from 'path';

const projectRoot = process.cwd();
const srcRoot = path.join(projectRoot, 'src');
const featuresRoot = path.join(srcRoot, 'features');

const allowedSharedFeatures = new Set(['shared', 'contracts']);

const importPatterns = [
  /(?:import|export)\s+[^'"]*from\s+['"]([^'"]+)['"]/g,
  /require\(\s*['"]([^'"]+)['"]\s*\)/g,
];

const scriptExtensions = new Set(['.ts', '.tsx', '.js', '.jsx']);

const isScriptFile = (filePath: string) => scriptExtensions.has(path.extname(filePath));

const walk = (dir: string): string[] => {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(full));
      continue;
    }
    if (!isScriptFile(full)) continue;
    files.push(full);
  }
  return files;
};

const resolveImport = (specifier: string, fromFile: string): string | null => {
  if (specifier.startsWith('.')) {
    return path.resolve(path.dirname(fromFile), specifier);
  }
  if (specifier.startsWith('@/')) {
    return path.join(srcRoot, specifier.slice(2));
  }
  if (specifier.startsWith('src/')) {
    return path.join(projectRoot, specifier);
  }
  return null;
};

const getFeatureFromPath = (filePath: string): string | null => {
  const relative = path.relative(featuresRoot, filePath);
  if (relative.startsWith('..')) return null;
  const parts = relative.split(path.sep);
  return parts[0] || null;
};

const isFeatureImportViolation = (
  fromFeature: string,
  resolvedImport: string
): { isViolation: boolean; targetFeature?: string } => {
  const targetFeature = getFeatureFromPath(resolvedImport);
  if (!targetFeature) return { isViolation: false };
  if (targetFeature === fromFeature) return { isViolation: false };
  if (allowedSharedFeatures.has(targetFeature)) return { isViolation: false };
  return { isViolation: true, targetFeature };
};

const files = walk(featuresRoot);
const violations: { file: string; importPath: string; targetFeature?: string }[] = [];

for (const file of files) {
  const fromFeature = getFeatureFromPath(file);
  if (!fromFeature) continue;
  const content = fs.readFileSync(file, 'utf8');

  for (const pattern of importPatterns) {
    const matches = content.matchAll(pattern);
    for (const match of matches) {
      const specifier = match[1];
      if (!specifier) continue;
      const resolved = resolveImport(specifier, file);
      if (!resolved) continue;
      const { isViolation, targetFeature } = isFeatureImportViolation(
        fromFeature,
        resolved
      );
      if (isViolation) {
        violations.push({ file, importPath: specifier, targetFeature });
      }
    }
  }
}

if (violations.length > 0) {
  console.error('Feature boundary violations detected:');
  violations.forEach(v => {
    const rel = path.relative(projectRoot, v.file);
    console.error(`- ${rel}: imports "${v.importPath}" (feature "${v.targetFeature}")`);
  });
  process.exit(1);
}

console.log('Feature boundary check passed.');
