# Component Guidelines

## Size Limits

- **Maximum**: 200 lines per component
- **Ideal**: 50-100 lines
- **Extract when**: > 3 responsibilities or > 3 useEffect hooks

## Responsibility Checklist

✅ Each component should have ONE primary responsibility:

- Display data
- Handle user input
- Manage form state
- Control layout

## Extraction Triggers

Split when component has:

1. Multiple unrelated UI sections
2. Complex conditional rendering branches
3. Multiple useEffect hooks for different concerns
4. More than 3-5 props that aren't related
