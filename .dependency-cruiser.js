/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'Circular dependencies make code harder to understand and maintain',
      from: {},
      to: {
        circular: true,
      },
    },
    {
      name: 'no-cross-layer-goblins-to-apps',
      severity: 'error',
      comment: 'GoblinOS packages should not depend on ForgeTM or Obsidian',
      from: {
        path: '^GoblinOS/packages/(goblins|cli)/',
      },
      to: {
        path: '^(ForgeTM|Obsidian)/',
      },
    },
    {
      name: 'no-orphans',
      severity: 'warn',
      comment: 'Orphan modules are likely dead code',
      from: {
        orphan: true,
        pathNot: [
          '(^|/)\\.[^/]+\\.(js|cjs|mjs|ts|json)$', // dot files
          '\\.d\\.ts$',                             // TypeScript declaration files
          '(^|/)tsconfig\\.json$',                 // TypeScript config
          '(^|/)package\\.json$',                  // package.json
        ],
      },
      to: {},
    },
    {
      name: 'no-deprecated-core',
      severity: 'warn',
      comment: 'Deprecated Node.js core modules should not be used',
      from: {},
      to: {
        dependencyTypes: ['core'],
        path: [
          '^(punycode|domain|constants|sys|_stream_wrap)$',
        ],
      },
    },
  ],
  options: {
    doNotFollow: {
      path: ['node_modules', 'dist', 'coverage', '.venv'],
    },
    tsPreCompilationDeps: true,
    tsConfig: {
      fileName: 'tsconfig.json',
    },
    enhancedResolveOptions: {
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default'],
    },
    reporterOptions: {
      dot: {
        collapsePattern: 'node_modules/(@[^/]+/[^/]+|[^/]+)',
      },
      archi: {
        collapsePattern: '^(packages|src)/[^/]+|node_modules/(@[^/]+/[^/]+|[^/]+)',
      },
      text: {
        highlightFocused: true,
      },
    },
  },
};
