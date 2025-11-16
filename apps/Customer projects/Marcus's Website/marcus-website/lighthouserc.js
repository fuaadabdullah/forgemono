module.exports = {
  ci: {
    collect: {
      staticDistDir: '.next',
      url: ['http://127.0.0.1:3000'],
      numberOfRuns: 1,
      settings: {
        chromeFlags: ['--no-sandbox', '--headless'],
      }
    },
    upload: {
      target: 'filesystem',
      outputDir: './lighthouse-ci',
    },
    assert: {
      assertions: {
        'categories:performance': ['error', {minScore: 0.75}],
        'categories:accessibility': ['error', {minScore: 0.9}],
        'categories:best-practices': ['error', {minScore: 0.8}],
      }
    }
  }
};
