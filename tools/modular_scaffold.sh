#!/usr/bin/env bash
# Simple scaffolding tool for creating a modular component
# Usage: ./tools/modular_scaffold.sh <path/to/module>

set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <relative/path/to/module>"
  exit 1
fi

ROOT_DIR="apps/goblin-assistant/src/components"
TARGET="$ROOT_DIR/$1"

mkdir -p "$TARGET"

NAME=$(basename "$TARGET")
cat > "$TARGET/$NAME.tsx" <<EOF
import React from 'react';
import './${NAME}.css';

interface ${NAME^}Props { prop?: string }

export const ${NAME^}: React.FC<${NAME^}Props> = ({ prop }) => {
  return <div className="$NAME">{prop}</div>;
};

export default ${NAME^};
EOF

cat > "$TARGET/utils.ts" <<EOF
export const exampleUtil = (s: string) => s.trim();
EOF

cat > "$TARGET/${NAME}.css" <<EOF
.${NAME} { padding: 8px; }
EOF

cat > "$TARGET/index.ts" <<EOF
export { default as ${NAME^} } from './${NAME}';
export * from './utils';
EOF

cat > "$TARGET/${NAME}.test.tsx" <<EOF
import React from 'react';
import { render } from '@testing-library/react';
import { ${NAME^}, exampleUtil } from './index';

test('scaffold test', () => {
  const utilText = exampleUtil(' hello ');
  expect(utilText).toBe('hello');
});
EOF

echo "Created module at $TARGET"
