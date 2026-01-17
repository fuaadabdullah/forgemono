# 🚀 Sandbox Feature - Quick Access Guide

## For End Users (Customers)

### 📍 Where to Find the Sandbox

#### Option 1: Direct Navigation
```
URL: https://your-domain.com/sandbox
```
Simply navigate to the `/sandbox` route directly in your browser.

#### Option 2: From Chat Interface
1. Go to the chat page (`/chat`)
2. Look at the top header
3. Click the **"Sandbox"** button (purple/pink gradient with code icon 💻)
4. You'll be taken to the sandbox page

#### Option 3: Navigation Menu (Coming Soon)
- Will be added to the main navigation menu
- Link from home page features section

---

## For Admins (Internal Use)

### 📍 Admin Sandbox Dashboard
```
URL: https://your-domain.com/admin/sandbox
```

The admin version includes:
- Same execution capabilities
- API endpoint documentation
- Technical details
- Direct API testing

---

## 🎯 What Can Users Do?

### ✅ Execute Python Code Safely
- Write Python code in the editor
- Click "Run Code" or press `Ctrl+Enter`
- See output in real-time with execution time

### ✅ Learn from Examples
- **Hello World** - Basic print statements
- **Math Operations** - Arithmetic calculations
- **Fibonacci** - Generate sequences
- **List Comprehension** - Work with lists
- **Dictionaries** - Data structures
- **String Manipulation** - Text processing

### ✅ Save and Manage Code
- Save snippets with custom names
- View execution history (last 10 runs)
- Load saved snippets instantly

### ✅ Safe Experimentation
The sandbox blocks dangerous operations:
- ❌ No file system access
- ❌ No network requests
- ❌ No subprocess execution
- ✅ Standard library available
- ✅ 30-second timeout for safety

---

## 📱 Mobile Friendly

Works perfectly on:
- Desktop computers
- Tablets
- Mobile phones
- All modern browsers

---

## 🔐 Security

### What's Allowed
- Standard Python syntax
- Math operations
- Data structures (lists, dicts, sets)
- String manipulation
- Control flow (loops, if/else)
- Standard library (math, random, datetime)

### What's Blocked
- File operations (open, read, write)
- Network access (requests, urllib)
- System commands (os, subprocess)
- Dangerous imports

---

## 💡 Use Cases

### For Learners
- Practice Python basics
- Test algorithms
- Learn data structures
- Experiment with syntax

### For Developers
- Quick code validation
- Algorithm testing
- Data manipulation experiments
- Math calculations

### For Educators
- Demonstrate Python concepts
- Share example code
- Interactive coding lessons
- Safe environment for students

---

## 🎨 User Interface

```
┌─────────────────────────────────────────────────────────────┐
│  [← Back to Chat]  Python Sandbox  [Language] [🟢 Live]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ℹ️ Safe Python Execution                                  │
│  Run Python code in a secure sandbox environment.          │
│  Press Ctrl+Enter to execute.                              │
│                                                             │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  Examples    │  Code Editor                                │
│  ├ Hello     │  ┌────────────────────────────────────────┐ │
│  ├ Math      │  │ print("Hello World!")                  │ │
│  ├ Fibonacci │  │                                        │ │
│  ├ Lists     │  │                                        │ │
│  └ Strings   │  │                                        │ │
│              │  │                                        │ │
│  History     │  │                                        │ │
│  └ Last 10   │  └────────────────────────────────────────┘ │
│              │  [Save] [Clear] [▶ Run Code]               │
│  Saved       │                                              │
│  └ Your code │  Output:                                     │
│              │  ┌────────────────────────────────────────┐ │
│  Limits      │  │ Hello World!                           │ │
│  ✓ Std lib   │  │ Execution time: 120ms                  │ │
│  ✓ 30s       │  └────────────────────────────────────────┘ │
│  ✗ Files     │                                              │
│  ✗ Network   │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + Enter` | Execute code |
| `Ctrl/Cmd + S` | Save snippet |
| `Esc` | Clear selection |

---

## 📊 Features at a Glance

| Feature | User Sandbox | Admin Sandbox |
|---------|--------------|---------------|
| Code Execution | ✅ | ✅ |
| Examples | ✅ | ✅ |
| Save Snippets | ✅ | ✅ |
| Execution History | ✅ | ✅ |
| API Documentation | ❌ | ✅ |
| Technical Details | ❌ | ✅ |

---

## 🔄 Current Status

- **Backend**: ✅ Live at `https://goblin-backend.fly.dev/execute/code`
- **Frontend**: ✅ Deployed at `/sandbox`
- **Chat Integration**: ✅ Sandbox button in chat header
- **Admin Panel**: ✅ Available at `/admin/sandbox`
- **Mobile Support**: ✅ Fully responsive
- **Security**: ✅ All dangerous operations blocked

---

## 📝 Next Steps for Users

1. Navigate to `/sandbox` or click the Sandbox button in chat
2. Try the "Hello World" example
3. Experiment with other examples
4. Write your own Python code
5. Save useful snippets for later
6. Share feedback with the team

---

**Questions?** Contact the Goblin Assistant support team or check the documentation at `/docs/sandbox`

