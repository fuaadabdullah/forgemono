# Accessibility Guide

This document describes the accessibility standards, implementation guidelines, and best practices for the GoblinOS Assistant frontend application.

## ♿ Accessibility Overview

We are committed to making the GoblinOS Assistant accessible to all users, including those with disabilities. Our goal is to meet **WCAG 2.1 Level AA** compliance standards across all frontend components and user interfaces.

## 🎯 Accessibility Principles

### WCAG 2.1 Guidelines

We follow the **POUR** principles:

- **Perceivable**: Information and UI components must be presentable to users in ways they can perceive
- **Operable**: UI components and navigation must be operable
- **Understandable**: Information and the operation of the user interface must be understandable
- **Robust**: Content must be robust enough to be interpreted reliably by a wide variety of user agents

### Compliance Standards

- **Target**: WCAG 2.1 Level AA
- **Screen Reader Support**: NVDA, JAWS, VoiceOver
- **Keyboard Navigation**: Full keyboard accessibility
- **Color Contrast**: Minimum 4.5:1 for normal text, 3:1 for large text
- **Focus Management**: Clear focus indicators and logical tab order

## 🏗️ Accessible Component Patterns

### 1. Buttons and Links

```tsx
// ✅ Good: Accessible button implementation
interface ButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  disabled?: boolean;
  ariaLabel?: string;
}

export function Button({ 
  children, 
  onClick, 
  variant = 'primary', 
  disabled = false,
  ariaLabel 
}: ButtonProps) {
  return (
    <button
      className={`btn btn-${variant} ${disabled ? 'btn-disabled' : ''}`}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      aria-disabled={disabled}
    >
      {children}
    </button>
  );
}

// Usage examples
<Button onClick={handleClick}>Click me</Button>
<Button onClick={handleClose} ariaLabel="Close modal">✕</Button>
<Button onClick={handleSubmit} disabled>Saving...</Button>
```

### 2. Forms and Inputs

```tsx
// ✅ Good: Accessible form implementation
interface FormFieldProps {
  label: string;
  id: string;
  type?: 'text' | 'email' | 'password' | 'textarea';
  value: string;
  onChange: (value: string) => void;
  error?: string;
  required?: boolean;
  helpText?: string;
}

export function FormField({
  label,
  id,
  type = 'text',
  value,
  onChange,
  error,
  required = false,
  helpText,
}: FormFieldProps) {
  const inputProps = {
    id,
    value,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => 
      onChange(e.target.value),
    required,
    'aria-describedby': [
      error && `${id}-error`,
      helpText && `${id}-help`,
    ].filter(Boolean).join(' ') || undefined,
    'aria-invalid': error ? 'true' : undefined,
  };

  return (
    <div className="form-field">
      <label htmlFor={id} className="form-label">
        {label}
        {required && <span aria-label="required">*</span>}
      </label>
      
      {type === 'textarea' ? (
        <textarea {...inputProps} className="form-textarea" />
      ) : (
        <input {...inputProps} type={type} className="form-input" />
      )}
      
      {helpText && (
        <div id={`${id}-help`} className="form-help">
          {helpText}
        </div>
      )}
      
      {error && (
        <div id={`${id}-error`} className="form-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}
```

### 3. Modal Dialogs

```tsx
// ✅ Good: Accessible modal implementation
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const initialFocusRef = useRef<HTMLElement | null>(null);

  // Focus management
  useEffect(() => {
    if (isOpen) {
      // Store current focus
      initialFocusRef.current = document.activeElement as HTMLElement;
      
      // Focus on modal after render
      setTimeout(() => {
        modalRef.current?.focus();
      }, 0);
    } else if (initialFocusRef.current) {
      // Return focus to previously focused element
      initialFocusRef.current.focus();
    }
  }, [isOpen]);

  // Trap focus within modal
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        const focusableElements = modalRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements) {
          const firstElement = focusableElements[0] as HTMLElement;
          const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
          
          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              e.preventDefault();
              lastElement.focus();
            }
          } else {
            if (document.activeElement === lastElement) {
              e.preventDefault();
              firstElement.focus();
            }
          }
        }
      }
      
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="modal-overlay" 
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={onClose}
    >
      <div 
        ref={modalRef}
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
      >
        <div className="modal-header">
          <h2 id="modal-title">{title}</h2>
          <button 
            className="modal-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>
        <div className="modal-body">
          {children}
        </div>
        <div className="modal-footer">
          <Button onClick={onClose}>Close</Button>
        </div>
      </div>
    </div>
  );
}
```

### 4. Navigation and Menus

```tsx
// ✅ Good: Accessible navigation implementation
export function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const menuItems = [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Providers', href: '/providers' },
    { label: 'Settings', href: '/settings' },
  ];

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex((prev) => (prev + 1) % menuItems.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex((prev) => (prev - 1 + menuItems.length) % menuItems.length);
        break;
      case 'Home':
        e.preventDefault();
        setActiveIndex(0);
        break;
      case 'End':
        e.preventDefault();
        setActiveIndex(menuItems.length - 1);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        window.location.href = menuItems[activeIndex].href;
        break;
    }
  };

  return (
    <nav aria-label="Main navigation">
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-controls="main-menu"
      >
        Menu
      </button>
      
      <ul 
        id="main-menu"
        className={`menu ${isOpen ? 'menu-open' : ''}`}
        role="menu"
        aria-hidden={!isOpen}
      >
        {menuItems.map((item, index) => (
          <li key={item.label} role="none">
            <a
              href={item.href}
              role="menuitem"
              aria-current={window.location.pathname === item.href}
              onKeyDown={(e) => handleKeyDown(e, index)}
              onMouseEnter={() => setActiveIndex(index)}
              className={activeIndex === index ? 'menu-item-active' : ''}
            >
              {item.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
```

## 🎨 Visual Design Accessibility

### Color and Contrast

```css
/* ✅ Good: High contrast color scheme */
:root {
  --text-primary: #1f2937; /* Dark gray for body text */
  --text-secondary: #4b5563; /* Medium gray for secondary text */
  --text-on-dark: #ffffff; /* White text on dark backgrounds */
  
  --bg-primary: #ffffff; /* White background */
  --bg-secondary: #f9fafb; /* Light gray background */
  --bg-tertiary: #111827; /* Dark background */
  
  --border-default: #e5e7eb; /* Light border */
  --border-strong: #9ca3af; /* Darker border for emphasis */
  
  /* Semantic colors with good contrast */
  --success: #16a34a; /* Green */
  --warning: #d97706; /* Orange */
  --error: #dc2626; /* Red */
  --info: #2563eb; /* Blue */
}

/* Focus indicators */
*:focus {
  outline: 3px solid #2563eb;
  outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  :root {
    --text-primary: #000000;
    --text-secondary: #333333;
    --bg-primary: #ffffff;
    --border-default: #000000;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Typography and Spacing

```css
/* ✅ Good: Accessible typography */
html {
  font-size: 16px; /* Base font size */
  line-height: 1.5; /* Good line height for readability */
}

h1, h2, h3, h4, h5, h6 {
  line-height: 1.2;
  margin-bottom: 0.5em;
}

/* Text sizing that respects user preferences */
body {
  font-size: clamp(14px, 1.2vw, 18px);
}

/* Sufficient spacing */
p, li, div {
  margin-bottom: 1em;
}

/* Touch target sizes (minimum 44px) */
button, a, input {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 16px;
}
```

## 🔍 Screen Reader Support

### ARIA Labels and Roles

```tsx
// ✅ Good: Proper ARIA implementation
export function SearchComponent() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div role="search" aria-label="Site search">
      <label htmlFor="search-input">Search</label>
      <div className="search-input-group">
        <input
          id="search-input"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-describedby="search-help"
          aria-autocomplete="list"
          aria-expanded={results.length > 0}
          aria-controls="search-results"
        />
        <button 
          type="submit"
          aria-label="Search"
          disabled={isLoading}
        >
          🔍
        </button>
      </div>
      
      <div id="search-help" className="sr-only">
        Type to search. Use arrow keys to navigate results.
      </div>
      
      {isLoading && (
        <div role="status" aria-live="polite">
          Searching...
        </div>
      )}
      
      {results.length > 0 && (
        <ul 
          id="search-results"
          role="listbox"
          aria-label="Search results"
        >
          {results.map((result) => (
            <li key={result.id} role="option">
              <a href={result.url}>{result.title}</a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### Live Regions

```tsx
// ✅ Good: Live region for dynamic content
export function NotificationArea() {
  const [notifications, setNotifications] = useState([]);

  // Announce new notifications to screen readers
  const addNotification = (message: string, type: 'success' | 'error' | 'info') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    
    // Remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  return (
    <>
      <button onClick={() => addNotification('Item saved successfully', 'success')}>
        Save
      </button>
      
      <div 
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {notifications.map(notification => (
          <div key={notification.id} role="alert">
            {notification.message}
          </div>
        ))}
      </div>
      
      {/* Visual notifications */}
      <div className="notifications">
        {notifications.map(notification => (
          <div 
            key={notification.id}
            className={`notification notification-${notification.type}`}
            role="alert"
          >
            {notification.message}
          </div>
        ))}
      </div>
    </>
  );
}
```

## ⌨️ Keyboard Navigation

### Focus Management

```tsx
// ✅ Good: Focus management utilities
import { useEffect, useRef } from 'react';

// Hook for managing focus
export function useFocusManagement() {
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const saveFocus = () => {
    previousFocusRef.current = document.activeElement as HTMLElement;
  };

  const restoreFocus = () => {
    if (previousFocusRef.current) {
      previousFocusRef.current.focus();
      previousFocusRef.current = null;
    }
  };

  const focusFirstElement = (container: HTMLElement | null) => {
    if (!container) return;
    
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    firstElement?.focus();
  };

  return { saveFocus, restoreFocus, focusFirstElement };
}

// Usage in modal
export function Modal({ isOpen, onClose, children }: ModalProps) {
  const { saveFocus, restoreFocus, focusFirstElement } = useFocusManagement();
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      saveFocus();
      setTimeout(() => {
        focusFirstElement(modalRef.current);
      }, 0);
    } else {
      restoreFocus();
    }
  }, [isOpen]);
  
  // ... rest of modal implementation
}
```

### Keyboard Shortcuts

```tsx
// ✅ Good: Accessible keyboard shortcuts
export function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only trigger shortcuts when not typing in input fields
      const activeElement = document.activeElement as HTMLElement;
      const isTyping = activeElement?.tagName === 'INPUT' || 
                       activeElement?.tagName === 'TEXTAREA' || 
                       activeElement?.contentEditable === 'true';

      if (isTyping) return;

      switch (e.key) {
        case 'Escape':
          // Close modals, dropdowns, etc.
          const closeable = document.querySelector('[data-close-on-escape]');
          if (closeable) {
            (closeable as HTMLElement).click();
          }
          break;
        
        case '/':
          // Focus search (if not typing)
          if (!isTyping) {
            const searchInput = document.getElementById('search-input');
            searchInput?.focus();
          }
          break;
        
        case 'k':
        case 'p':
          // Command palette (common pattern)
          if (e.ctrlKey || e.metaKey) {
            // Open command palette
            console.log('Open command palette');
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);
}
```

## 🧪 Accessibility Testing

### Automated Testing

```tsx
// ✅ Good: Accessibility testing setup
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Accessibility Tests', () => {
  it('Button has no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Form has no accessibility violations', async () => {
    const { container } = render(
      <FormField
        label="Email"
        id="email"
        type="email"
        value=""
        onChange={() => {}}
      />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Modal has no accessibility violations', async () => {
    const { container } = render(
      <Modal isOpen={true} onClose={() => {}} title="Test Modal">
        Modal content
      </Modal>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Manual Testing Checklist

#### Screen Reader Testing

- [ ] **NVDA (Windows)**: Test with Firefox and Chrome
- [ ] **JAWS (Windows)**: Test with Internet Explorer and Chrome
- [ ] **VoiceOver (Mac)**: Test with Safari and Chrome
- [ ] **TalkBack (Android)**: Test with Chrome
- [ ] **VoiceOver (iOS)**: Test with Safari

#### Keyboard Navigation Testing

- [ ] **Tab Navigation**: All interactive elements are reachable
- [ ] **Shift+Tab**: Reverse navigation works correctly
- [ ] **Arrow Keys**: Navigate within components (menus, modals)
- [ ] **Enter/Space**: Activate buttons and links
- [ ] **Escape**: Close modals and dropdowns
- [ ] **Home/End**: Navigate to beginning/end of content

#### Visual Testing

- [ ] **Color Contrast**: Use tools like WebAIM Contrast Checker
- [ ] **Text Scaling**: Test up to 200% zoom
- [ ] **Browser Zoom**: Test up to 400% zoom
- [ ] **High Contrast Mode**: Test Windows high contrast mode
- [ ] **Reduced Motion**: Test with `prefers-reduced-motion: reduce`

### Testing Tools

#### Browser Extensions

- **axe DevTools**: Automated accessibility testing
- **WAVE**: Web accessibility evaluation
- **Lighthouse**: Performance and accessibility audits
- **Color Oracle**: Color blindness simulation

#### Command Line Tools

```bash
# axe CLI for automated testing
npm install -g axe-cli
axe http://localhost:3000

# Pa11y for automated accessibility testing
npm install -g pa11y
pa11y http://localhost:3000

# Lighthouse CI
npm install -g @lhci/cli@0.12.x
lhci autorun
```

## 📱 Mobile Accessibility

### Touch Targets

```css
/* ✅ Good: Mobile touch targets */
.touch-target {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 16px;
  margin: 4px 0;
}

/* Spacing between touch targets */
.touch-target + .touch-target {
  margin-top: 8px;
}
```

### Mobile Screen Readers

```tsx
// ✅ Good: Mobile accessibility considerations
export function MobileAccessibleComponent() {
  return (
    <div>
      {/* Large touch targets */}
      <button 
        className="mobile-button"
        aria-label="Large button for easy tapping"
        style={{
          minHeight: '44px',
          minWidth: '44px',
          fontSize: '18px',
          padding: '16px',
        }}
      >
        Tap me
      </button>
      
      {/* Clear visual hierarchy */}
      <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>
        Main Title
      </h1>
      
      <p style={{ fontSize: '16px', lineHeight: '1.5' }}>
        Body text with good readability
      </p>
      
      {/* Avoid hover-only interactions */}
      <div 
        role="button"
        tabIndex={0}
        onClick={() => {}}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            // Handle both click and keyboard
          }
        }}
      >
        Interactive element
      </div>
    </div>
  );
}
```

## 🔧 Accessibility Utilities

### Custom Hooks

```tsx
// ✅ Good: Accessibility utility hooks
import { useEffect, useRef } from 'react';

// Hook for announcing messages to screen readers
export function useAnnouncement() {
  const liveRegionRef = useRef<HTMLDivElement>(null);

  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (liveRegionRef.current) {
      liveRegionRef.current.setAttribute('aria-live', priority);
      liveRegionRef.current.textContent = message;
      
      // Clear after a short delay
      setTimeout(() => {
        if (liveRegionRef.current) {
          liveRegionRef.current.textContent = '';
        }
      }, 1000);
    }
  };

  return { announce, liveRegionRef };
}

// Hook for managing focus trap
export function useFocusTrap(isActive: boolean) {
  const containerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [isActive]);

  return containerRef;
}
```

### Accessibility Components

```tsx
// ✅ Good: Reusable accessible components
export function SkipLink() {
  return (
    <a 
      href="#main-content"
      className="skip-link"
    >
      Skip to main content
    </a>
  );
}

export function VisuallyHidden({ children }: { children: React.ReactNode }) {
  return (
    <span className="sr-only" role="status" aria-live="polite">
      {children}
    </span>
  );
}

export function FocusTrap({ children }: { children: React.ReactNode }) {
  const containerRef = useFocusTrap(true);
  
  return (
    <div ref={containerRef} tabIndex={-1}>
      {children}
    </div>
  );
}
```

## 📚 Additional Resources

### Official Guidelines

- [WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Learn/Accessibility)

### Testing Tools

- [axe DevTools](https://www.deque.com/axe/)
- [WAVE Evaluation Tool](https://wave.webaim.org/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Lighthouse](https://developer.chrome.com/docs/lighthouse/overview/)

### Learning Resources

- [A11y Project](https://www.a11yproject.com/)
- [Accessibility Weekly](https://accessibilityweekly.net/)
- [Inclusive Components](https://inclusive-components.design/)

### Community

- [A11y Slack](https://join.slack.com/t/a11y/shared_invite/zt-1jhbz8a2q-0XtK~I5WEv3rX7L~rDR~tg)
- [Accessibility on Twitter](https://twitter.com/search?q=%23a11y)
- [WebAIM Discussion Forums](https://webaim.org/discussion/)

---

**Remember**: Accessibility is an ongoing process, not a one-time implementation. Regularly test with real users and assistive technologies to ensure your application remains accessible to everyone.
