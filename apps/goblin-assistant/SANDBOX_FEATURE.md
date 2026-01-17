# Python Sandbox Feature

## Overview

The Goblin Assistant now includes a **Python Sandbox** feature that allows users to safely execute Python code in an isolated environment. This is perfect for:

- Testing algorithms and data structures
- Learning Python programming
- Quick code validation
- Data manipulation experiments
- Mathematical calculations

## User Access Points

### 1. Direct URL
Users can access the sandbox directly at:
```
https://your-domain.com/sandbox
```

### 2. From Chat Interface
While in the chat interface (`/chat`), users can:
- Click the **"Sandbox"** button in the header (purple/pink gradient button with code icon)
- This provides quick access without leaving the application

### 3. From Home Page
Users will see the sandbox mentioned in the features/use cases section

## Features

### Code Editor
- **Full Python syntax support** with monospace font
- **Line-by-line editing** in a textarea
- **Keyboard shortcuts:**
  - `Ctrl/Cmd + Enter`: Execute code
  - `Ctrl/Cmd + S`: Save snippet

### Example Codes
Pre-built examples to get started:
- Hello World
- Math Operations
- Fibonacci Sequence
- List Comprehension
- Dictionary Operations
- String Manipulation

### Execution Features
- **Real-time execution** via `/execute/code` API endpoint
- **Output display** with execution time tracking
- **Error handling** with clear error messages
- **Copy output** functionality

### Save & History
- **Save snippets** locally with custom names
- **Execution history** (last 10 executions)
- **Quick load** from saved snippets

### Security Limits
✅ **Allowed:**
- Standard library modules (math, random, datetime, etc.)
- Data structures (lists, dicts, sets)
- String operations
- Mathematical operations
- Control flow (loops, conditionals)

❌ **Blocked:**
- File system access (`open`, `read`, `write`)
- Network operations (`requests`, `urllib`)
- Subprocess execution (`os.system`, `subprocess`)
- Dangerous imports (`os`, `sys`, `subprocess`)
- 30-second timeout on execution

## Technical Details

### Backend API
- **Endpoint**: `POST https://goblin-backend.fly.dev/execute/code`
- **Request Body**: `{ "code": "print('hello')" }`
- **Response**: `{ "success": true, "output": "hello\n", "executionTime": 120 }`

### Security Implementation
Located in `/api/execute_router.py`:
- Python subprocess isolation
- Base64 encoding for safe code transmission
- Pattern-based blocking of dangerous imports
- 30-second execution timeout
- No file system or network access

### Frontend Implementation
Located in `/app/sandbox/page.tsx`:
- React hooks for state management
- localStorage for snippet persistence
- Responsive layout (desktop + mobile)
- Real-time execution feedback

## Admin Dashboard

Admins have an additional sandbox view at:
```
/admin/sandbox
```

This provides the same functionality but with more detailed technical information and API documentation.

## User Experience Flow

1. **Landing** → User opens `/sandbox`
2. **Write Code** → User types or selects an example
3. **Execute** → Click "Run Code" or press `Ctrl+Enter`
4. **View Output** → See results with execution time
5. **Save** (optional) → Save useful snippets for later
6. **Return** → Click "Back to Chat" to return to chat interface

## Mobile Support

The sandbox is fully responsive:
- Touch-friendly buttons
- Scrollable code editor
- Collapsible sidebar on mobile
- Optimized for tablets and phones

## Future Enhancements

Potential improvements:
- [ ] Multi-language support (JavaScript, Ruby, etc.)
- [ ] Collaborative editing
- [ ] Share snippets via URL
- [ ] Import/export code files
- [ ] Syntax highlighting
- [ ] Auto-completion
- [ ] Code formatting
- [ ] Unit testing support

## Monitoring

The sandbox feature is monitored via:
- Backend execution logs
- Error tracking in `/execute/code` endpoint
- Usage analytics (execution count, popular examples)
- Performance metrics (execution time distribution)

---

**Last Updated**: January 17, 2026
**Status**: ✅ Live in Production
