# Copilot Instructions - Bus Booking Platform

**Project:** Django + Next.js bus booking marketplace  
**Standards:** Enterprise-level with error tracking system  
**Usage:** Repository-level (autocomplete) + Chat (interactive assistant)

---

## 🎯 CORE MISSION

Write **production-grade code** with:
- ✅ Self-documenting comments
- ✅ Error codes for instant debugging
- ✅ Type safety (Python type hints, TypeScript interfaces)
- ✅ Security & performance by default
- ✅ SOLID + DRY principles

**Quality gate:** "Would this pass Google code review?"

---

## 🚨 ERROR CODE SYSTEM (MANDATORY)

**Every error MUST have a unique code from ERROR_REGISTRY.md**

### Format: `[APP]-[FILE]-[TYPE]-[NUMBER]`

```
Examples:
- BUS-MODELS-VAL-001
- BOK-SERV-CONFLICT-003
- PAY-CASH-API-002

APP: USR, BUS, BOK, PAY, REV, DOC, COM
FILE: MODELS, VIEWS, SERV, SERIAL, UTILS
TYPE: VAL, PERM, DB, API, AUTH, NOTFOUND, CONFLICT, CONFIG
```

### Error Code Template:

```python
# Error Code: [APP]-[FILE]-[TYPE]-[NUMBER]
# Message: [Clear error message]
# Cause: [Why this happens]
# Solution: [How to fix]
if condition:
    raise ValidationError(
        "Clear error message",
        code='[APP]-[FILE]-[TYPE]-[NUMBER]'
    )
```

---

## 📝 COMMENTING STANDARDS

### Rule 1: Function Docstrings (MANDATORY)

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    One-line summary.
    
    Detailed explanation of what this does and why it exists.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        ReturnType: What is returned
    
    Raises:
        ErrorType (ERROR-CODE): When this happens
    
    Example:
        >>> result = function_name('value', 123)
        >>> print(result)
        'output'
    
    Performance/Database:
        - Database queries: 2
        - Avg time: 50ms
    """
```

### Rule 2: Inline Comments (Critical Logic Only)

```python
# Step 1: Lock bus row to prevent concurrent bookings
# Using select_for_update() creates database-level lock
# Prevents race condition where two customers book same bus
bus = Bus.objects.select_for_update().get(id=bus_id)

# Step 2: Check availability
# AvailabilityBlock acts as calendar - one block = one booked date
if AvailabilityBlock.objects.filter(bus=bus, date=date).exists():
    # Error Code: BOK-SERV-CONFLICT-001
    # Message: Bus not available on selected date
    # Cause: Another booking exists for this date
    # Solution: Choose different date or different bus
    raise ValidationError(
        f"Bus {bus.name} not available on {date}",
        code='BOK-SERV-CONFLICT-001'
    )
```

### Rule 3: Explain WHY, Not WHAT

```python
# ❌ BAD (states the obvious):
# Set status to pending
booking.status = 'pending'

# ✅ GOOD (explains reasoning):
# Status starts as 'pending_payment' - changes to 'confirmed' after Cashfree webhook
# This prevents operator from seeing unconfirmed bookings
booking.status = Booking.Status.PENDING_PAYMENT
```

---

## 🐍 DJANGO CODE RULES

### Models - Required Elements:

```python
class ModelName(models.Model):
    """Brief description of what this model represents."""
    
    # TextChoices for status fields
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
    
    # Type hints + help_text on all fields
    name: str = models.CharField(
        max_length=200,
        help_text="Display name"
    )
    
    # ForeignKey with db_index + related_name
    operator: 'User' = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='buses',
        db_index=True
    )
    
    # Timestamps (MANDATORY)
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['operator', 'status']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.id})"
    
    def save(self, *args, **kwargs):
        # Always run validation before save
        self.full_clean()
        super().save(*args, **kwargs)
```

### ViewSets - Required Elements:

```python
class ModelViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for Model.
    
    Endpoints: GET/POST/PATCH/DELETE /api/models/
    Permissions: [Who can access]
    Error Codes: [APP]-VIEWS-*
    """
    serializer_class = ModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    def get_queryset(self) -> QuerySet:
        """Optimized query with role filtering."""
        # Prevent N+1 queries
        qs = Model.objects.select_related('fk_field').prefetch_related('m2m_field')
        
        # Role-based filtering
        if self.request.user.role == 'operator':
            return qs.filter(operator=self.request.user)
        return qs
    
    def create(self, request) -> Response:
        """Create via service layer."""
        # Validate
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Business logic in service (NOT here)
        try:
            obj = ModelService.create_model(
                data=serializer.validated_data,
                user=request.user
            )
        except ValidationError as e:
            return Response(
                {'error': str(e), 'code': e.code},
                status=400
            )
        
        return Response(
            self.get_serializer(obj).data,
            status=201
        )
```

### Services - Required Pattern:

```python
class ModelService:
    """Business logic for Model operations."""
    
    @staticmethod
    @transaction.atomic
    def create_with_side_effects(data: dict, user: User) -> Model:
        """
        Create Model and related records atomically.
        
        Steps:
        1. [Step description]
        2. [Step description]
        
        Error Codes:
        - [APP]-SERV-VAL-001: [Description]
        - [APP]-SERV-CONFLICT-001: [Description]
        """
        # Implementation with inline comments
        pass
```

---

## ⚛️ REACT/NEXT.JS CODE RULES

### Components - Required Elements:

```typescript
'use client';

import { useState, useCallback, memo } from 'react';
import Image from 'next/image';
import { Type } from '@/types';

interface ComponentProps {
  prop1: Type;
  onAction: (data: Type) => void;
}

/**
 * Component description.
 * 
 * Features:
 * - [Feature 1]
 * - [Feature 2]
 * 
 * @example
 * <Component prop1={value} onAction={handleAction} />
 */
export const Component = memo(function Component({
  prop1,
  onAction
}: ComponentProps) {
  // State with purpose comment
  const [data, setData] = useState<Type | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Memoized callback (prevents re-renders)
  const handleAction = useCallback(() => {
    onAction(data);
  }, [data, onAction]);
  
  // Loading state
  if (loading) {
    return <div className="animate-pulse">Loading...</div>;
  }
  
  // Error state
  if (error) {
    return (
      <div className="p-4 bg-red-50 rounded">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }
  
  // Main UI with semantic HTML + Tailwind
  return (
    <article 
      className="p-4 bg-white rounded-lg shadow"
      aria-label="Component description"
    >
      <Image
        src={data.image || '/placeholder.jpg'}
        alt={data.name}
        width={400}
        height={200}
        className="rounded"
      />
      
      <button
        onClick={handleAction}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        aria-label="Action description"
      >
        Action
      </button>
    </article>
  );
});
```

---

## 🔒 SECURITY RULES (NON-NEGOTIABLE)

```python
# Rule 1: Validate ALL input
try:
    value = int(request.data.get('field'))
    if value <= 0:
        raise ValueError
except (TypeError, ValueError):
    # Error Code: COM-UTILS-VAL-001
    raise ValidationError("Invalid format", code='COM-UTILS-VAL-001')

# Rule 2: Check permissions ALWAYS
if object.owner != request.user:
    # Error Code: [APP]-VIEWS-PERM-001
    raise PermissionDenied("Access denied", code='[APP]-VIEWS-PERM-001')

# Rule 3: Use ORM (never raw SQL)
✅ Model.objects.filter(id=value)  # Auto-escaped
❌ f"SELECT * FROM table WHERE id={value}"  # SQL injection!

# Rule 4: Sanitize HTML
from django.utils.html import escape
safe_html = escape(user_input)
```

---

## ⚡ PERFORMANCE RULES

```python
# Query Optimization (MANDATORY)

# ❌ WRONG (N+1 queries):
buses = Bus.objects.all()
for bus in buses:
    print(bus.operator.name)  # +1 query per bus

# ✅ CORRECT (2 queries total):
buses = Bus.objects.select_related('operator').prefetch_related('photos').all()
for bus in buses:
    print(bus.operator.name)  # No extra queries

# Guidelines:
# - select_related: ForeignKey, OneToOne
# - prefetch_related: ManyToMany, reverse ForeignKey
# - Add db_index=True on filtered fields
# - Use pagination for large lists
```

---

## 🚨 ANTI-PATTERNS (PREVENT IMMEDIATELY)

```python
# Django
❌ fields = '__all__'  → ✅ Explicit field list
❌ Model.objects.all()  → ✅ .select_related().prefetch_related()
❌ Business logic in views → ✅ Move to services.py
❌ f"SQL {var}"  → ✅ Use ORM
❌ No type hints  → ✅ Add type hints
❌ No error codes  → ✅ Add error codes with comments
❌ Hardcoded values  → ✅ Use constants/settings
❌ Missing docstrings  → ✅ Add comprehensive docstrings

# React/TypeScript
❌ style={{ ... }}  → ✅ Tailwind classes
❌ any type  → ✅ Proper interfaces
❌ Unhandled errors  → ✅ try/catch with user feedback
❌ <img>  → ✅ <Image>
❌ Missing loading states  → ✅ Add loading/error UI
❌ Hardcoded URLs  → ✅ Environment variables
```

---

## 📋 CODE GENERATION CHECKLIST

Before suggesting code, verify:

- [ ] **Error codes** on all raised errors
- [ ] **Error comments** (Code/Message/Cause/Solution)
- [ ] **Docstring** with Args/Returns/Raises/Example
- [ ] **Type hints** (Python) or **interfaces** (TypeScript)
- [ ] **Inline comments** on complex logic
- [ ] **Business logic** in services.py (NOT views.py)
- [ ] **Query optimization** (select_related/prefetch_related)
- [ ] **Permission checks** on all endpoints
- [ ] **Input validation** on all user data
- [ ] **Error handling** with try/except
- [ ] **Loading/error states** in React
- [ ] **Accessibility** (ARIA labels, semantic HTML)
- [ ] **Tailwind classes** (no inline styles)
- [ ] **Next.js Image** (not <img>)

---

## 🎓 TEACHING MODE (Copilot Chat)

### When user asks "How do I...?"

Structure answer as:

```
1. QUICK ANSWER (code snippet)

2. EXPLANATION (why this approach)

3. EXAMPLE (from our bus booking project)
   # Concrete example with our models/components

4. GOTCHAS (common mistakes)
   ❌ Don't do this
   ✅ Do this instead

5. RELATED (links to docs, alternatives)
```

### When user asks you to review code:

Check for:
1. **Error codes** present on all errors?
2. **Comments** explain WHY not WHAT?
3. **Type safety** (no `any` types)?
4. **Performance** (queries optimized)?
5. **Security** (input validated, permissions checked)?
6. **DRY** (no code duplication)?
7. **SOLID** (single responsibility)?

Provide specific fixes with error codes.

---

## 💬 COMMUNICATION STYLE

### ❌ DON'T just give code:
```python
queryset = Bus.objects.select_related('operator').all()
```

### ✅ DO explain WHY:
```python
# Use select_related to prevent N+1 queries
# Without this: 100 buses = 101 database queries (1 for buses, 100 for operators)
# With this: 100 buses = 1 query (SQL JOIN fetches everything at once)
# Performance impact: 500ms → 50ms for 100 buses
queryset = Bus.objects.select_related('operator').all()
```

---

## 🎯 PROJECT CONTEXT

### Tech Stack:
- **Backend:** Django 5 + DRF (Heroku)
- **Frontend:** Next.js 14 App Router (Vercel)
- **Database:** Supabase (PostgreSQL)
- **Auth:** Supabase Auth (OTP)
- **Payments:** Cashfree
- **Storage:** Cloudinary
- **Maps:** Leaflet + OpenStreetMap

### File Structure:
```
Backend:
apps/[app]/
  ├── models.py      # DB models only
  ├── serializers.py # DRF serializers
  ├── views.py       # Thin controllers
  ├── services.py    # Business logic HERE
  └── admin.py

Frontend:
src/
  ├── app/           # Next.js routes
  ├── components/ui/ # Reusable components
  ├── lib/api.ts     # API client
  └── types/         # TypeScript interfaces
```

### Coding Conventions:
- **Python:** snake_case, Google docstrings
- **TypeScript:** camelCase, JSDoc comments
- **Styles:** Tailwind utility classes only
- **API:** RESTful with DRF ViewSets
- **Business Logic:** services.py (never in views.py)

### Business Context:
- Two-sided marketplace (customers + operators)
- Core entities: User, Bus, Booking, Payment, Review
- Flow: Search → Select → Book → Pay → Rate
- Key challenges: Availability management, double-booking prevention, disintermediation

---

## 📚 ERROR REGISTRY

**All error codes defined in:** `ERROR_REGISTRY.md`

**Quick reference:**
- `USR-*`: Users app errors
- `BUS-*`: Buses app errors
- `BOK-*`: Bookings app errors
- `PAY-*`: Payments app errors
- `REV-*`: Reviews app errors
- `DOC-*`: Documents app errors
- `COM-*`: Common/utility errors

**When adding new error:**
1. Find next number in `ERROR_REGISTRY.md`
2. Add row with Message/Cause/Solution
3. Use in code with comment block
4. Commit both files together

**When debugging:**
1. Find error code in logs (e.g., `BOK-SERV-CONFLICT-001`)
2. Search `ERROR_REGISTRY.md`
3. Read Cause + Solution
4. Go to specified file
5. Fix bug

---

## 🚀 PRODUCTION STANDARDS

**Every line of code should be:**
- ✅ **Type-safe** (typed everywhere)
- ✅ **Secure** (validated, authorized)
- ✅ **Performant** (optimized queries)
- ✅ **Documented** (docstrings, comments)
- ✅ **Testable** (pure functions, dependency injection)
- ✅ **Maintainable** (SOLID, DRY, clear naming)
- ✅ **Debuggable** (error codes, logging)

**Remember:**
- Code is read 10x more than written
- Write for the next developer (or yourself in 6 months)
- Comments prevent bugs by making intent clear
- Error codes save hours of debugging

**Quality gate:**
"Would this pass code review at Google, Meta, or Stripe?"

If NO → Revise before suggesting.

---

**END OF COPILOT INSTRUCTIONS**

*Version: 2.0 (Merged copilot + agent + error system)*  
*Last Updated: 2026-02-13*