# Commenting Guidelines

## When to Comment

✅ DO comment when:

- Explaining WHY (business logic, decisions)
- Documenting complex algorithms
- Warning about side effects
- Todo items with context
- Public API documentation

❌ DON'T comment:

- Obvious code ("i++" // increment i)
- Self-explanatory names
- Comments that duplicate code
- Outdated information

## Comment Types

1. **File Header** - Module purpose
2. **Function/Class** - JSDoc/TSDoc
3. **Inline** - Complex logic explanations
4. **TODO/FIXME** - With issue tracker link

## Templates

### File Header Template

```javascript
/**
 * @fileoverview User authentication service
 * @description Handles user login, registration, and session management
 * @author GoblinOS Team
 * @version 1.0.0
 */
```

### Function Documentation Template

````typescript
/**
 * Calculates the total price including tax and discounts.
 *
 * @param items - Array of item prices in cents
 * @param taxRate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @param discountCode - Optional discount code to apply
 *
 * @returns Final price in dollars, rounded to 2 decimals
 *
 * @example
 * ```typescript
 * const total = calculateTotal([1000, 2000], 0.08, 'SAVE10');
 * console.log(total); // 32.40
 * ```
 *
 * @throws {InvalidDiscountError} If discount code is invalid
 * @throws {NegativeValueError} If any price is negative
 *
 * @remarks
 * Prices are stored in cents to avoid floating-point errors.
 * Tax is applied after discounts per IRS regulations.
 */
function calculateTotal(items: number[], taxRate: number, discountCode?: string): number {
  // Implementation
}
````

### Component Documentation Template

````typescript
/**
 * UserProfile displays a user's information with edit capabilities.
 *
 * @component
 *
 * @param {Object} props
 * @param {User} props.user - The user object to display
 * @param {Function} props.onSave - Callback when user saves changes
 * @param {boolean} [props.isEditable=true] - Whether the profile can be edited
 *
 * @example
 * ```tsx
 * <UserProfile
 *   user={currentUser}
 *   onSave={handleSave}
 *   isEditable={hasPermission}
 * />
 * ```
 *
 * @remarks
 * Uses Formik for form state management.
 * Validation rules are defined in `userValidationSchema`.
 */
export const UserProfile: React.FC<UserProfileProps> = (
  {
    /* ... */
  }
) => {
  // Implementation
};
````

### Complex Logic Comments

```javascript
// Use binary search for O(log n) lookup instead of linear search
// This optimization is critical for performance with large datasets
const index = binarySearch(sortedArray, targetValue);
```

### TODO/FIXME Comments

```javascript
// TODO: Implement rate limiting for API endpoints
// Issue: https://github.com/fuaadabdullah/ForgeMonorepo/issues/123
// Context: Current implementation allows unlimited requests, need to prevent abuse

// FIXME: Temporary workaround for Safari date parsing bug
// Replace with proper Date constructor once Safari 14+ is minimum requirement
const safariSafeDate = new Date(dateString.replace(/-/g, '/'));
```

### Business Logic Explanations

```javascript
// Business Rule: Premium users get 2x faster response times
// This is a key differentiator in our pricing tiers
if (user.subscriptionTier === 'premium') {
  priorityQueue.push(request);
} else {
  standardQueue.push(request);
}
```

### Warning Comments

```javascript
// WARNING: This function modifies the input array in-place
// Always pass a copy if you need to preserve the original
function sortUsersByActivity(users) {
  // Implementation modifies users array directly
}
```
