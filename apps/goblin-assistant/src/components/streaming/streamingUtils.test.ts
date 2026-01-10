import { describe, it, expect } from '@jest/globals';
import { getNewChunk, detectCodeInText, toTokenChunk } from './streamingUtils';

describe('streamingUtils', () => {
  it('returns new chunk correctly', () => {
    expect(getNewChunk('', 'abc')).toBe('abc');
    expect(getNewChunk('ab', 'abc')).toBe('c');
    expect(getNewChunk('abc', 'abc')).toBe('');
    expect(getNewChunk('abc', '')).toBe('');
  });

  it('detects code segments', () => {
    expect(detectCodeInText('This is `code`')).toBe(true);
    expect(detectCodeInText('No code here')).toBe(false);
    expect(detectCodeInText('```block```')).toBe(true);
  });

  it('converts chunk to token chunk', () => {
    const chunk = toTokenChunk('Hello', 'Some `inline` code');
    expect(chunk.text).toBe('Hello');
    expect(typeof chunk.timestamp).toBe('number');
    expect(chunk.isCode).toBe(true);
  });
});
