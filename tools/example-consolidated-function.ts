// Example consolidated serverless function router
// This is a sample Node/TypeScript file demonstrating how to combine multiple
// serverless functions into a single Vercel function to avoid the 12 function limit.

import type { VercelRequest, VercelResponse } from '@vercel/node'

// Example handler functions that would normally be in separate files
async function handleItem(req: VercelRequest, res: VercelResponse) {
  // Example: implement logic here. For real code, import handler logic from lib/handlers
  res.status(200).json({ message: 'Handled /api/item' })
}

async function handleOther(req: VercelRequest, res: VercelResponse) {
  res.status(200).json({ message: 'Handled /api/other' })
}

const routes = new Map<string, (req: VercelRequest, res: VercelResponse) => Promise<void>>([
  ['/api/item', handleItem],
  ['/api/other', handleOther],
])

export default async function (req: VercelRequest, res: VercelResponse) {
  const url = new URL(req.url ?? '/', `http://${req.headers.host}`)
  const route = routes.get(url.pathname)
  if (!route) {
    res.status(404).json({ error: 'Not found' })
    return
  }
  try {
    await route(req, res)
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'internal error' })
  }
}
