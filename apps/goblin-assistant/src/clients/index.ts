// Export runtime clients
export { FastApiRuntimeClient } from './FastApiRuntimeClient';
export { MockRuntimeClient } from './MockRuntimeClient';

// Default runtime client instance
import { FastApiRuntimeClient } from './FastApiRuntimeClient';
import { MockRuntimeClient } from './MockRuntimeClient';

export const runtimeClient = new FastApiRuntimeClient();
export const runtimeClientDemo = new MockRuntimeClient();
