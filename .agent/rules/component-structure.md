---
trigger: always_on
---

Name: component-structure

Content:

1. Server Component (default):
   - No 'use client' directive
   - Async data fetching
   - No useState, useEffect
2. Client Component (only when needed):
   - 'use client' directive at top
   - For interactivity (onClick, forms, state)
   - Wrap with memo if re-renders are expensive
3. Component template:
   - TypeScript interface for props
   - JSDoc documentation
   - Error boundary wrapper
   - Loading state handling
   - Error state handling
4. Example:

```typescript
"use client";
import { memo } from "react";

interface Props {
  data: Data;
  onAction: () => void;
}

export const Component = memo(function Component({ data, onAction }: Props) {
  // Implementation
});
```
