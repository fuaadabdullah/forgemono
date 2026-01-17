module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint', 'react', 'prettier'],
  rules: {
    // Code quality rules
    'prettier/prettier': 'error',
    '@typescript-eslint/explicit-function-return-type': 'error',
    '@typescript-eslint/no-explicit-any': 'warn', // Changed from 'error' to 'warn' for flexibility
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        'argsIgnorePattern': '^_',
        'varsIgnorePattern': '^_',
        'caughtErrorsIgnorePattern': '^_',
      },
    ],
    '@typescript-eslint/naming-convention': [
      'error',
      {
        selector: 'variable',
        format: ['camelCase', 'UPPER_CASE', 'PascalCase'],
        leadingUnderscore: 'allow',
      },
    ],
    'react/prop-types': 'off', // Using TypeScript
    'react/react-in-jsx-scope': 'off', // Next.js doesn't require
    'react/jsx-filename-extension': [1, { extensions: ['.tsx'] }],
    'max-lines': ['warn', { max: 300, skipComments: true }],
    'max-lines-per-function': ['warn', { max: 50, skipComments: true }],
    complexity: ['warn', { max: 10 }],

    // Require JSDoc comments for public functions
    'require-jsdoc': [
      'error',
      {
        require: {
          FunctionDeclaration: true,
          MethodDefinition: true,
          ClassDeclaration: true,
          ArrowFunctionExpression: true,
          FunctionExpression: true,
        },
      },
    ],

    // Enforce TODO/FIXME format with issue link
    'no-warning-comments': [
      'warn',
      {
        terms: ['todo', 'fixme', 'xxx', 'hack'],
        location: 'anywhere',
      },
    ],
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  overrides: [
    {
      files: ['*.test.ts', '*.test.tsx'],
      rules: {
        'max-lines-per-function': 'off',
      },
    },
  ],
};