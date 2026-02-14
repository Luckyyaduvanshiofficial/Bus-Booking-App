# Bug Report – Bookings App Test Failures

**Date:** 2025-07-14  
**Environment:** Django 6.0.2 · Python 3.14.0 · SQLite (test DB)  
**Test File:** `backend/apps/bookings/tests.py` (1306 lines, 44 tests)  
**Result:** 40 PASSED · 3 FAILED · 1 ERROR  
**Severity:** HIGH — Bugs affect model validation and **payment refund flow**

---

## Summary

| # | Test Name | Status | Affected File | Bug Type |
|---|-----------|--------|---------------|----------|
| 1 | `test_bok_models_val_001_past_date` | **FAIL** | `models.py` L224 | Validation bypass |
| 2 | `test_cancel_booking_sets_refund_for_captured_payment` | **FAIL** | `services.py` L730–755 | Refund not processed |
| 3 | `test_cancel_booking_splits_refund_across_multiple_captured_payments` | **FAIL** | `services.py` L730–755 | Refund not processed |
| 4 | `test_cancel_booking_keeps_paid_status_when_refund_fails` | **ERROR** | `services.py` L730–755 | Refund record missing |

---

## Bug 1: Past-Date Validation Never Fires (UUIDField pk Issue)

### Test
```
FAIL: test_bok_models_val_001_past_date (apps.bookings.tests.BookingModelTest)
AssertionError: ValidationError not raised
```

### Location
- **Test:** `tests.py` line 99–109
- **Bug:** `models.py` line 224

### What the test does
```python
booking = Booking(
    customer=self.customer, operator=self.operator, bus=self.bus,
    trip_type='one_way', pickup_location='Jaipur',
    drop_location='Delhi', pickup_date=dt.date(2020, 1, 1),  # Past date
    pickup_time=dt.time(8, 0), passenger_count=10,
    base_amount=Decimal('4000'), total_amount=Decimal('4500'),
)
with self.assertRaises(DjangoValidationError):
    booking.clean()  # Expected: ValidationError. Actual: Nothing raised.
```

### Root Cause (CONFIRMED)
In `models.py` line 224, `clean()` has:
```python
if not self.pk and self.pickup_date and self.pickup_date < _date.today():
    raise ValidationError('Pickup date must be in the future.', code='BOK-MODELS-VAL-001')
```

But `Booking.id` is declared as:
```python
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
```

**Problem:** `default=uuid.uuid4` means a UUID is auto-generated at Python-level when the object is instantiated with `Booking(...)`, BEFORE it is saved to the database. So `self.pk` is NEVER `None`, even for unsaved objects. The guard `if not self.pk` is **always False**, and the past-date validation **never fires**.

### Fix
Replace line 224 in `models.py`:
```python
# BEFORE (broken):
if not self.pk and self.pickup_date and self.pickup_date < _date.today():

# AFTER (correct):
if self._state.adding and self.pickup_date and self.pickup_date < _date.today():
```

**Why this works:** Django's `self._state.adding` is `True` for objects that haven't been saved to the database yet, regardless of whether the pk has a value. This is the official Django way to check "is this a new object?"

### Impact
- **Current:** Any past date can be set on new bookings without validation.
- **Mitigated by:** `BookingService.create_booking()` calls `booking.full_clean()` before `booking.save()`, so this only matters if `clean()` is called directly or model is saved outside the service layer.
- **Also affects:** `Payment.save()` at line 428 has the same `if not self.pk` bug — the duplicate Payment check never runs. (Payment also uses `UUIDField(primary_key=True, default=uuid.uuid4)`.)

---

## Bugs 2–4: Refund Callback Not Executing / Silently Failing

These three bugs share the same root cause: the post-commit refund callback (`_refund_after_commit`) either **does not execute** or **fails silently** due to a broad `except Exception` handler.

### Code Flow
```
cancel_booking()  [@transaction.atomic]
  ├── booking.save(status=cancelled, refund_amount=X)
  └── PaymentService.schedule_booking_refund_post_commit(booking_id, amount, reason)
        └── transaction.on_commit(_refund_after_commit)   ← callback is deferred
              └── _refund_after_commit()
                    ├── process_booking_refund()
                    │   └── create_refund_record()
                    │       ├── Payment.objects.create(status='created')  ← refund Payment record
                    │       ├── _create_cashfree_refund()  ← mocked in tests
                    │       └── refund_payment.save(status='refunded'/'failed')
                    └── booking.save(payment_status='refunded')
```

All 3 tests use `self.captureOnCommitCallbacks(execute=True)` to execute the deferred callback:
```python
with self.captureOnCommitCallbacks(execute=True):
    booking = BookingService.cancel_booking(booking=booking, cancelled_by=self.customer)
```

---

### Bug 2: Refund Payment Status Not Updated After Successful Gateway Call

**Test:** `test_cancel_booking_sets_refund_for_captured_payment` (line 315)

```
FAIL: AssertionError: 'fully_paid' != <PaymentStatus.REFUNDED: 'refunded'>
```

**Expected:** After `cancel_booking`, `booking.payment_status` should be `REFUNDED`.  
**Actual:** `booking.payment_status` remains `'fully_paid'`.

**Mock:** `_create_cashfree_refund` returns `{'success': True, 'status_code': 202}`

The test also checks that a refund Payment record was created with `status=REFUNDED`. Since `payment_status` remains `fully_paid`, the entire `_refund_after_commit` callback likely never ran or failed silently.

---

### Bug 3: Multi-Payment Refund Split Not Working

**Test:** `test_cancel_booking_splits_refund_across_multiple_captured_payments` (line 460)

```
FAIL: AssertionError: 'fully_paid' != <PaymentStatus.REFUNDED: 'refunded'>
```

**Expected:** Refund split across 2 captured payments, each getting a refund Payment, `payment_status=REFUNDED`.  
**Actual:** `payment_status` remains `'fully_paid'`, no refund records created.

Same root cause as Bug 2.

---

### Bug 4: Failed Gateway Refund — No Payment Record Created

**Test:** `test_cancel_booking_keeps_paid_status_when_refund_fails` (line 367)

```
ERROR: apps.bookings.models.Payment.DoesNotExist: Payment matching query does not exist.
```

**Expected:** Gateway mock returns `{'success': False, 'reason': 'gateway_error'}`. The test expects:
- `booking.payment_status` stays `'fully_paid'` ✓ (this passes trivially since callback didn't run)
- A refund Payment record exists with `status=FAILED` ✗ (no record created at all)

**Actual:** `Payment.objects.get(booking=booking, payment_type='refund')` raises `DoesNotExist` because `_refund_after_commit` never created the refund Payment record.

---

### Root Cause Analysis (Bugs 2–4)

**Primary Suspect: `_refund_after_commit` callback not executing or silently swallowing errors.**

The callback is in `services.py` lines 733–755:
```python
def _refund_after_commit() -> None:
    try:
        booking = Booking.objects.get(pk=booking_id)
        refunded_total = PaymentService.process_booking_refund(
            booking=booking, amount=normalized_amount, reason=reason,
        )
        if refunded_total >= normalized_amount and ...:
            booking.payment_status = Booking.PaymentStatus.REFUNDED
            booking.save(update_fields=['payment_status'])
    except Booking.DoesNotExist:
        logger.warning(...)        # Silently logged
    except Exception:
        logger.exception(...)       # ← ALL errors silently caught and logged
```

**Possible causes (investigate in order):**

1. **`captureOnCommitCallbacks` + `@transaction.atomic` savepoint interaction:**  
   `cancel_booking` is decorated with `@transaction.atomic`, which creates a savepoint inside `TestCase`'s wrapping transaction. `transaction.on_commit()` inside the savepoint registers the callback to fire when the outer transaction commits. `captureOnCommitCallbacks` is supposed to intercept this, but there may be a Django version-specific issue with how callbacks are promoted from savepoints to the captured list. **Test:** Replace `TestCase` with `TransactionTestCase` for these 3 tests and see if they pass.

2. **`Payment.save()` calls `self.full_clean()` — possible validation error caught silently:**  
   `Payment.save()` (at line 398 of `models.py`) calls `self.full_clean()` on every save, including when `update_fields` is passed. If `full_clean()` raises any `ValidationError`, the broad `except Exception` in `_refund_after_commit` catches it, logs it, and returns — the test never sees the error.  
   Example: `Payment.save()` has a unique constraint check (`uniq_pending_payment_per_booking_type`) that runs during `validate_unique()`.

3. **`Payment.save()` checks `if not self.pk` (same UUID bug as Bug 1):**  
   Line 428 in `models.py`:
   ```python
   if not self.pk and self.booking_id:
       existing = Payment.objects.filter(...)
   ```
   This duplicate-payment check **never executes** because Payment also uses `UUIDField(primary_key=True)`. Not the direct cause of Bugs 2–4, but a related integrity issue.

### Recommended Investigation Steps

```python
# Step 1: Add a print inside _refund_after_commit to confirm if it's being called
def _refund_after_commit() -> None:
    print(f"[DEBUG] _refund_after_commit called for booking_id={booking_id}")
    try:
        ...
    except Exception as e:
        print(f"[DEBUG] _refund_after_commit EXCEPTION: {e}")  # ← SEE THE REAL ERROR
        logger.exception(...)
```

```python
# Step 2: If callback IS executing, temporarily remove the broad except to see the error
def _refund_after_commit() -> None:
    # try:  # ← Comment out for debugging
    booking = Booking.objects.get(pk=booking_id)
    refunded_total = PaymentService.process_booking_refund(...)
    ...
    # except Exception:  # ← Comment out for debugging
    #     logger.exception(...)
```

```python
# Step 3: If callback is NOT executing, use TransactionTestCase for these tests
from django.test import TransactionTestCase

class BookingServiceRefundTest(TransactionTestCase):
    """Refund tests that need real transaction commit behavior."""
    ...
```

### Suggested Fix (once root cause confirmed)
- **If `captureOnCommitCallbacks` issue:** Move refund tests to `TransactionTestCase`, or refactor the refund logic so it can be called synchronously for testing.
- **If `full_clean()` error:** Fix `Payment.save()` to skip `full_clean()` when `update_fields` is provided (only validate the fields being updated), or ensure the callback handles `ValidationError` explicitly.
- **Critical:** Remove or narrow the broad `except Exception` in `_refund_after_commit` — at minimum, re-raise or leave it only in production. Silent error swallowing makes debugging impossible.

---

## Additional Issue: `Payment.save()` Duplicate Check Never Runs

**Location:** `models.py` line 428  
**Severity:** MEDIUM

```python
# Payment.save() at line 428:
if not self.pk and self.booking_id:   # ← Same UUIDField bug
    existing = Payment.objects.filter(
        booking_id=self.booking_id,
        status__in=('captured', 'authorized'),
        payment_type=self.payment_type,
    ).exists()
    if existing:
        raise DjangoValidationError('Payment already processed', code='PAY-MODELS-CONFLICT-001')
```

**Problem:** `Payment.id` is also `UUIDField(primary_key=True, default=uuid.uuid4)`, so `not self.pk` is always `False`. This deduplication guard never runs. Duplicate payments could be created.

**Fix:** Same as Bug 1 — use `self._state.adding` instead of `not self.pk`.

---

## File Context for Backend Team

### `backend/apps/bookings/tests.py` (1306 lines)
- **9 test classes, 44 test methods**
- Uses `TestCase` (not `TransactionTestCase`) — wraps everything in a rolled-back transaction
- Uses `captureOnCommitCallbacks(execute=True)` to manually trigger `on_commit` callbacks
- Uses `@patch('apps.bookings.services.PaymentService._create_cashfree_refund', ...)` to mock the Cashfree gateway
- **Key test classes for these bugs:**
  - `BookingModelTest` (line 78): Tests model validation — Bug 1 here
  - `BookingServiceTest` (line 186): Tests booking lifecycle including cancellation/refund — Bugs 2–4 here

### `backend/apps/bookings/models.py` (569 lines)
- `Booking` model (line 19): `id = UUIDField(primary_key=True, default=uuid.uuid4)` — Bug 1 source
- `Booking.clean()` (line 206): Validates pickup_date, return_date, amount, capacity — Bug 1 at line 224
- `Booking.save()` (line 261): Custom save generates `booking_number` with random suffix. Does NOT call `clean()`/`full_clean()` to avoid double validation.
- `Booking.calculate_refund()` (line 301): Full refund if >48h before pickup, 50% if >24h, 0 otherwise.
- `Payment` model (line 323): Also uses `UUIDField(primary_key=True)` — same pk issue
- `Payment.save()` (line 398): Calls `self.full_clean()`, has duplicate check with `if not self.pk` bug

### `backend/apps/bookings/services.py` (1293 lines)
- `BookingService.create_booking()` (line 37): Creates booking, calls `full_clean()` before save
- `BookingService.cancel_booking()` (line 290): `@transaction.atomic`, calculates refund, saves status, schedules refund via `on_commit`
- `PaymentService.schedule_booking_refund_post_commit()` (line 722): Registers `_refund_after_commit` via `transaction.on_commit()` — the deferred callback that's not executing
- `PaymentService.process_booking_refund()` (line 762): Iterates captured payments, creates refund records
- `PaymentService.create_refund_record()` (line 674): Creates refund Payment, calls gateway, updates status
- `PaymentService._create_cashfree_refund()` (line 860): Actual Cashfree API call (mocked in tests)
- **Critical:** `_refund_after_commit` inner function (line 733) has a broad `except Exception` that silently logs errors — this is the direct reason bugs 2–4 are hard to diagnose

### `backend/apps/bookings/tasks.py` (108 lines)
- `expire_pending_bookings()` (line 82): Celery task that expires stale pending bookings
- `_expire_single_pending_booking()` (line 22): Also uses `schedule_booking_refund_post_commit()` — same refund callback. If bugs 2–4 are a code issue (not test-only), this task's refund flow is also affected in production.

---

## Version Mismatch Warning

| Item | Actual (Runtime) | Declared |
|------|-------------------|----------|
| Python | 3.14.0 | `runtime.txt`: 3.11.8 |
| Django | 6.0.2 | `requirements.txt`: 5.0.1 |

These mismatches could cause subtle behavioral differences. Ensure `requirements.txt` and `runtime.txt` are updated to match the actual running versions.

---

## Priority Recommendation

1. **P0 (Fix Now):** Bug 1 — Replace `if not self.pk` with `if self._state.adding` in `models.py` lines 224 and 428. This is a 2-line fix.
2. **P0 (Investigate Now):** Bugs 2–4 — Add debug prints in `_refund_after_commit` to identify whether the callback runs and what exception is caught. This blocks the entire refund flow.
3. **P1:** Remove or narrow the broad `except Exception` in `_refund_after_commit` (line 750). At minimum, add explicit error types instead of catching everything.
4. **P2:** Update `requirements.txt` and `runtime.txt` to match actual versions.

---

*Generated by automated test analysis — 2025-07-14*
