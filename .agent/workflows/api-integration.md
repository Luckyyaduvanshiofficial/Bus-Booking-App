---
description: api-integration
---

Create a new API integration with:

1. TypeScript interface matching Django serializer
2. SWR hook for GET requests
3. Mutation function for POST/PUT/DELETE
4. Error handling with backend error codes
5. Loading skeleton component
6. Error display component

Example:

```typescript
// types/api.ts
interface Bus {
  id: string;
  name: string;
  price_per_km: string; // Django Decimal
}

// hooks/useBuses.ts
export function useBuses() {
  const { data, error, isLoading } = useSWR<Bus[]>("/buses/", fetcher);
  return { buses: data, error, isLoading };
}
```

Follow global rules for error handling and TypeScript.
