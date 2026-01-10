export interface TokenChunk {
  text: string;
  isCode: boolean;
  timestamp: number;
}

// Returns the new substring that appears after `last` in `streamingText`.
export const getNewChunk = (last: string, streamingText: string): string => {
  if (!last) return streamingText || '';
  if (!streamingText || streamingText.length <= last.length) return '';
  return streamingText.slice(last.length);
};

export const detectCodeInText = (text: string): boolean => {
  if (!text) return false;
  return text.includes('```') || text.includes('`');
};

export const toTokenChunk = (chunk: string, streamingText: string): TokenChunk => ({
  text: chunk,
  isCode: detectCodeInText(streamingText),
  timestamp: Date.now(),
});
