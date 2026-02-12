export const BRAND_NAME = 'Goblin Assistant';

export const BRAND_TAGLINE = 'Feed the Goblin. Get your mind back.';

export const HOME_VALUE_PROPS = [
  {
    title: 'Chew through docs',
    body: 'Drop in notes, PDFs, meeting logs, or a wall of text. Get the signal.',
    icon: '📚',
  },
  {
    title: 'Summon decisions',
    body: 'Turn messy context into action items, risks, and next steps.',
    icon: '🧭',
  },
  {
    title: 'Keep your memory',
    body: 'Threads and snippets stay organized so you can pick up where you left off.',
    icon: '🗄️',
  },
] as const;

export const HOME_EXAMPLE_CARDS = [
  {
    title: 'Turn chaos into a plan',
    body: '“Summarize this PRD into decisions, risks, and next steps.”',
    icon: '🧱',
  },
  {
    title: 'Write the update for you',
    body: '“Draft a short stakeholder update from these bullet points.”',
    icon: '📝',
  },
  {
    title: 'Debug faster',
    body: '“Explain this stack trace and suggest the most likely fix.”',
    icon: '🛠️',
  },
] as const;

export const CHAT_COMPOSER_PLACEHOLDER =
  'Feed the Goblin: paste context, ask for a summary, extract action items...';

export const CHAT_COMPOSER_TIP =
  'Try: summarize, extract risks, draft a reply, build a checklist.';

export const CHAT_QUICK_PROMPTS = [
  {
    label: 'Decisions + actions',
    prompt: 'Summarize this into decisions and action items. Keep it tight.',
  },
  {
    label: 'Risks + unknowns',
    prompt: 'Find risks, unknowns, and assumptions in this plan. Suggest fixes.',
  },
  {
    label: 'Stakeholder update',
    prompt: 'Draft a short status update for stakeholders. Include next steps.',
  },
  {
    label: 'Debug this',
    prompt: 'Explain this error log and propose 3 likely fixes with reasoning.',
  },
] as const;

export const SEARCH_QUICK_QUERIES = [
  'API rate limit policy',
  'Incident runbook',
  'Contract termination clause',
  'Quarterly roadmap',
] as const;
