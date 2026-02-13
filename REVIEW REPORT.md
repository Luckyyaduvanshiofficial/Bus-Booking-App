# COMPREHENSIVE CODE AUDIT REPORT

**Project:** Bus Booking Platform (Django/DRF backend)  
**Audit Date:** 2026-02-13  
**Audited Scope:** `backend/apps/**/*.py`, `backend/bus_booking/settings.py`, `Docs/ERROR_REGISTRY.md`  
**Method:** Static security/financial/race-condition/quality audit + repository error-code checker (`scripts/check_error_codes.py`)
                                                     
---

## EXECUTIVE SUMMARY

**Launch Recommendation:** **BLOCK** (fix criticals first)

**Why:** Multiple exploitable authorization and concurrency flaws can cause unauthorized data modification and financial/state inconsistencies under concurrent requests.

**Critical blockers (P0):**
1. Broken object-level authorization in bus management (`buses/views.py`).
2. Payment initiation idempotency race (duplicate payment records/orders).
3. Booking completion race (double counter increments).
4. Payment confirmation race (duplicate state transitions/history writes).

---

## SECURITY VULNERABILITIES (PASS 1)

### 1) Broken Object-Level Authorization in Bus APIs (P0)

- **Severity:** P0 (account-level integrity breach)
- **Files/Lines:**
  - `backend/apps/buses/views.py:66` (`class BusViewSet`)
  - `backend/apps/buses/views.py:79` (`get_permissions` → default `IsAuthenticated`)
  - `backend/apps/buses/views.py:125` (`perform_create` only; no update/destroy ownership check)
  - `backend/apps/buses/views.py:179` (`BusPhotoViewSet`)
  - `backend/apps/buses/views.py:203` (`BusAmenityViewSet`)
  - `backend/apps/buses/views.py:227` (`AvailabilityBlockViewSet`)
- **Issue:** Ownership checks are enforced on create for nested resources, but **not consistently enforced for update/delete/retrieve** paths.
- **Exploit:** Any authenticated non-owner can attempt:
  - `PATCH /api/v1/buses/<other_operator_bus_id>/`
  - `DELETE /api/v1/buses/<bus_id>/photos/<photo_id>/`
  - `DELETE /api/v1/buses/<bus_id>/availability/<block_id>/`
- **Business Impact:** Competitor sabotage, unauthorized listing edits/deletions, potential overbooking by removing blocks.

**Recommended Fix (root-cause):**
- Add explicit object-level ownership checks in `update`, `partial_update`, `destroy` across `BusViewSet`, `BusPhotoViewSet`, `BusAmenityViewSet`, `AvailabilityBlockViewSet`.
- Reuse `BusOwnershipMixin.check_bus_permission()` in all mutating handlers.
- Add custom object permission class (`IsBusOwnerOrAdmin`) and apply consistently.

**Unit test proving fix**
```python
def test_bus_update_non_owner_forbidden():
    """Verify horizontal privilege escalation is blocked"""
    # Arrange: customer (or another operator) + someone else's bus
    # Act: PATCH /api/v1/buses/{foreign_bus_id}/
    # Assert: 403 with BUS-VIEWS-PERM-002
```

**Related Issues:**
- Similar pattern in: `buses/views.py` nested ViewSets (`BusPhotoViewSet`, `BusAmenityViewSet`, `AvailabilityBlockViewSet`)
- Depends on: centralized object-permission policy

---

### 2) Payment Initiation Race (Duplicate Pending Payments) (P0)

- **Severity:** P0 (financial consistency)
- **Files/Lines:**
  - `backend/apps/bookings/services.py:418` (`existing_pending = Payment.objects.filter(...).first()`)
  - `backend/apps/bookings/services.py:432` (`Payment.objects.create(...)`)
- **Issue:** “Idempotency guard” is non-atomic; concurrent requests can both miss `existing_pending` and create duplicates.
- **Exploit:** Rapid double-click/retry storms create multiple payment records/orders for same booking.
- **Business Impact:** Duplicate order generation, reconciliation complexity, possible customer confusion/charge retries.

**Recommended Fix (root-cause):**
- Lock booking row (`select_for_update`) in `initiate_payment`.
- Add DB-level uniqueness guarantee for active pending payment per `(booking, payment_type, status='created')` (partial unique index or equivalent strategy).
- Return existing pending record post-lock.

**Unit test proving fix**
```python
def test_duplicate_payment_initiation_prevented_under_race():
    """Verify double-click payment race creates only one pending payment"""
    # Run two concurrent initiate_payment calls for same booking
    # Assert only one 'created' payment exists
```

**Related Issues:**
- Similar pattern in: payment confirmation race
- Depends on: transaction lock discipline + DB unique constraints

---

### 3) Booking Completion Race Causes Double Counters (P0)

- **Severity:** P0 (data integrity)
- **Files/Lines:**
  - `backend/apps/bookings/services.py:320` (`complete_booking`)
  - `backend/apps/bookings/services.py:337` (`if booking.status != 'confirmed'`)
  - `backend/apps/bookings/services.py:353` (customer counter increment)
  - `backend/apps/bookings/services.py:356` (bus trip increment)
- **Issue:** No row-level lock / compare-and-swap on booking status before side-effects.
- **Exploit:** Two concurrent complete requests can both pass status check and increment counters twice.
- **Business Impact:** Inflated KPI/analytics, payout/reputation distortion.

**Recommended Fix (root-cause):**
- Lock booking row (`select_for_update`) before transition.
- Transition with conditional update (`WHERE status='confirmed'`) and verify rows updated == 1.
- Execute side-effects only once.

**Unit test proving fix**
```python
def test_complete_booking_race_prevented():
    """Verify concurrent completion does not double-increment counters"""
    # Fire parallel complete requests
    # Assert booking completed once; counters increment exactly once
```

**Related Issues:**
- Similar pattern in: `respond_to_booking`, `cancel_booking`
- Depends on: uniform state-transition locking strategy

---

### 4) Payment Confirmation/Webhook Race (P0/P1)

- **Severity:** P0 for consistency, P1 for observability drift
- **Files/Lines:**
  - `backend/apps/bookings/views.py:485` (`Payment.objects.select_related('booking').get(id=order_id)`)
  - `backend/apps/bookings/services.py:587` (`if payment.status == 'captured'` in-memory guard)
- **Issue:** Confirmation path does not lock payment row; duplicate simultaneous webhook/manual confirm can pass stale status checks.
- **Exploit:** Concurrent replay/delivery causes duplicate history writes and unpredictable branch behavior.
- **Business Impact:** Ledger/event noise, hard reconciliation, false incident alerts.

**Recommended Fix (root-cause):**
- Re-read payment under `select_for_update` inside `confirm_payment` transaction.
- Use atomic status transition (`update ... where status != 'captured'`).
- Keep idempotent response semantics in webhook.

**Unit test proving fix**
```python
def test_webhook_duplicate_delivery_idempotent():
    """Verify duplicate payment success webhooks do not duplicate state changes"""
    # Replay same success webhook concurrently
    # Assert one state transition/history entry
```

**Related Issues:**
- Similar pattern in: payment initiation race
- Depends on: lock-first, write-once payment state machine

---

### 5) Production Security Defaults Unsafe by Default (P1)

- **Severity:** P1
- **Files/Lines:**
  - `backend/bus_booking/settings.py:25` (`DEBUG` default True)
  - `backend/bus_booking/settings.py:244` (`SECURE_SSL_REDIRECT` default False)
  - `backend/bus_booking/settings.py:250` (`SECURE_HSTS_SECONDS` default 0)
  - `backend/bus_booking/settings.py:178` (`CORS_ALLOW_CREDENTIALS = True`)
- **Issue:** Deployment can accidentally run without transport hardening.
- **Exploit:** Misconfigured prod can expose cookies/session/token transport over insecure channels.

**Recommended Fix:**
- Fail-safe defaults for production (`DEBUG=False`, `SECURE_SSL_REDIRECT=True`, non-zero HSTS).
- Add environment mode guard enforcing secure settings in non-local environments.

**Unit test proving fix**
```python
def test_production_security_settings_enforced():
    """Verify prod settings cannot start with insecure transport defaults"""
    # Assert secure flags enabled when ENV=production
```

**Related Issues:**
- Similar pattern in: missing CSP/Referrer-Policy checks (see Production section)

---

## FINANCIAL/PAYMENT BUGS (PASS 2)

### F1) Duplicate pending payments under race (P0)
- Location: `bookings/services.py:418,432`
- Risk: Multiple pending rows/order creations for same booking.
- Fix: booking lock + DB uniqueness on pending state.

### F2) Invalid `payment_method` can bubble as server error (P1)
- Location: `bookings/views.py` `initiate()` path (raw `request.data.get('payment_method')`), `bookings/services.py:432`
- Risk: Invalid payment method may hit model validation exceptions unexpectedly.
- Fix: Add dedicated serializer for initiate endpoint with strict choices and mapped error code (`PAY-VIEWS-VAL-*`).

### F3) Broad exception catches in payment confirm paths reduce diagnosability (P2)
- Location: `bookings/views.py:373`, `bookings/views.py:519`
- Risk: Incident triage slower; harder to differentiate known validation vs system faults.
- Fix: Catch explicit exceptions; preserve codes in responses/logs.

### F4) Cashfree order creation has timeout but no retry strategy (P2)
- Location: `bookings/services.py` Cashfree `_create_cashfree_order`
- Risk: transient network failures increase checkout drop-off.
- Fix: bounded retry with backoff for safe idempotent create paths.

---

## DATA INTEGRITY & RACE CONDITIONS (PASS 3)

### D1) Booking completion race (P0)
- Location: `bookings/services.py:320-366`
- Impact: double counters/history.

### D2) Booking respond/cancel transitions not lock-guarded (P1)
- Location: `bookings/services.py` transition methods
- Impact: concurrent transition conflicts, non-deterministic final state.

### D3) Single-day block creation can throw unhandled integrity conflicts (P1)
- Location: `bookings/services.py:130` (`AvailabilityBlock.objects.create`)
- Impact: concurrent block insert from parallel actor can raise IntegrityError (500).
- Fix: use `get_or_create` consistently or catch IntegrityError and map to `BOK-SERV-CONFLICT-001`.

### D4) Payment confirmation idempotency check is non-atomic (P1)
- Location: `bookings/services.py:587`
- Impact: duplicate processing windows under concurrency.

---

## BUSINESS LOGIC ERRORS (PASS 4)

### B1) Document upload endpoint does not enforce operator/admin role (P2)
- Location: `users/views.py` `DocumentViewSet.perform_create`
- Impact: customers can create owner-level docs (`bus=None`), polluting verification queue.
- Fix: enforce role check + error code.

### B2) Expired-token specific code is overwritten by generic auth handler (P2)
- Location: `common/authentication.py` emits `USR-VIEWS-AUTH-003`; `common/exceptions.py` maps AuthenticationFailed to `USR-VIEWS-AUTH-002`
- Impact: loss of precise incident/debug signal.
- Fix: preserve explicit code from exception when available.

### B3) `apps/payments/*` service layer absent despite registry section (P2)
- Observation: payment logic embedded in `apps/bookings/*`; `ERROR_REGISTRY.md` includes `PAY-SERV-*` and `PAY-VIEWS-*` as if standalone app exists.
- Impact: architecture/documentation drift and maintenance confusion.

---

## ERROR CODE COVERAGE ANALYSIS (PASS 5)

**Source:** `backend/scripts/check_error_codes.py` run during audit

### Implementation Status: 86/133 matched (64.7%)

- Registry entries: **133**
- Implemented in code: **94**
- Matched (in registry + code): **86**
- Registry-only (planned/unimplemented): **47**
- In code but not in registry: **8**

### Missing Error Codes (examples, high-priority)
| Code | File Should Be In | Error Type | Priority |
|------|-------------------|------------|----------|
| BOK-SERV-DB-002 | bookings/services.py | Race retry path | P1 |
| PAY-SERV-DB-001 | bookings/services.py | Payment update DB failure | P1 |
| PAY-SERV-API-002 | bookings/views.py / services.py | Webhook signature validation flow | P1 |
| REV-VIEWS-PERM-001 | reviews/views.py | Review ownership permission | P2 |
| DOC-VIEWS-VAL-001 | users/views.py | Document upload validation | P2 |

### Unregistered Errors (in code, not in registry)
| Code | File | Example Line |
|------|------|--------------|
| BOK-SERV-PERM-001 | apps/bookings/services.py | 405 |
| BOK-SERV-VAL-002 | apps/bookings/services.py | 236 |
| BOK-SERV-VAL-003 | apps/bookings/services.py | 679 |
| BOK-SERV-VAL-004 | apps/bookings/services.py | 689 |
| BOK-SERV-VAL-005 | apps/bookings/services.py | 699 |
| BOK-SERV-VAL-006 | apps/bookings/services.py | 711 |
| USR-SERV-API-001 | apps/users/services.py | 45 |
| USR-VIEWS-PERM-004 | apps/users/permissions.py | 80 |

---

## CODE QUALITY ISSUES (PASS 6)

1. **Overbroad exception handling** in critical paths (`bookings/views.py`, `users/views.py`) reduces observability.
2. **Inconsistent permission enforcement strategy** (create-time checks only in several ViewSets).
3. **Architecture drift** between docs/registry and app boundaries (payments in bookings app).
4. **State transition logic duplicated in service branches** without centralized finite-state transition guard.

---

## PRODUCTION READINESS (PASS 7)

### Checklist Results

**Security Headers:** ⚠️ PARTIAL
- Present: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`
- Missing/Not enforced by default: robust HSTS (`SECURE_HSTS_SECONDS=0` default), explicit CSP policy, strict referrer policy.
- Fix: enforce secure defaults in production env profile.

**Configuration:** ❌ FAIL (for default production safety)
- `DEBUG` default True (`settings.py:25`)
- `SECURE_SSL_REDIRECT` default False (`settings.py:244`)
- `SECURE_HSTS_SECONDS` default 0 (`settings.py:250`)

**Concurrency Hardening:** ❌ FAIL
- Critical financial/booking transitions not lock-safe under concurrent requests.

**Error-Code Discipline:** ⚠️ PARTIAL
- 64.7% matched; undocumented in-code codes exist.

**Testing of critical adversarial paths:** ❌ FAIL
- Missing race/concurrency and webhook replay/idempotency tests.

---

## FILE-BY-FILE ANALYSIS

### apps/bookings/services.py
- **Grade:** C
- **LOC:** 773
- **Issues Found:** 8
- **Highlights:** Uses `@transaction.atomic`; good pricing decomposition.
- **Critical Gaps:** non-atomic idempotency (`418`), no lock in confirm flow (`587`), completion race (`337-356`), single-day block create conflict (`130`).

### apps/bookings/views.py
- **Grade:** B-
- **LOC:** 575
- **Issues Found:** 5
- **Highlights:** Webhook signature check + amount verification exists.
- **Gaps:** no lock on payment fetch (`485`), broad exceptions (`373`, `519`), invalid JSON and internal errors without dedicated error-code mapping.

### apps/buses/views.py
- **Grade:** D
- **LOC:** 248
- **Issues Found:** 6
- **Critical Gaps:** object-level authorization missing for update/destroy across bus and nested endpoints.

### apps/buses/services.py
- **Grade:** B
- **LOC:** 153
- **Issues Found:** 2
- **Gaps:** race resilience relies on caller behavior; no DB-level conflict wrapping for all paths.

### apps/users/services.py
- **Grade:** B-
- **LOC:** 328
- **Issues Found:** 3
- **Highlights:** role-escalation guard in register path.
- **Gaps:** broad exception handling around OTP API integration.

### apps/users/views.py
- **Grade:** B
- **LOC:** 312
- **Issues Found:** 3
- **Gaps:** document upload role gate missing; broad exception in verify endpoint.

### apps/common/authentication.py
- **Grade:** B+
- **LOC:** 72
- **Issues Found:** 1
- **Gap:** expired-token code can be masked by exception handler.

### apps/common/exceptions.py
- **Grade:** B-
- **LOC:** 85
- **Issues Found:** 2
- **Gap:** generic auth mapping loses specificity; not all validation responses normalized to structured code paths.

### apps/reviews/views.py
- **Grade:** B+
- **LOC:** 188
- **Issues Found:** 1
- **Gap:** generally solid; minor consistency opportunities only.

### backend/bus_booking/settings.py
- **Grade:** C
- **LOC:** 360+
- **Issues Found:** 4
- **Gap:** unsafe-by-default prod posture.

---

## N+1 QUERY REPORT

**Total N+1 Issues Found:** 2 (potential)

1. **`BookingDetailSerializer.get_history`**
   - File: `apps/bookings/serializers.py`
   - Pattern: per-object query (`obj.history.order_by`) if ever used in list-like contexts.
   - Impact: can scale poorly if serializer reused for collections.
   - Fix: prefetch `history` and use prefetched cache path.

2. **`BusDetailSerializer.get_blocked_dates`**
   - File: `apps/buses/serializers.py`
   - Pattern: query per bus object.
   - Impact: potential N+1 if serializer used for multi-object responses.
   - Fix: prefetch availability blocks for detail lists or move field to dedicated endpoint.

---

## MISSING TEST COVERAGE

**Critical Flows Without Tests:**
1. Concurrent payment initiation race (duplicate pending payments).
2. Concurrent booking completion race (double increments).
3. Webhook duplicate/replay idempotency under parallel delivery.
4. Unauthorized bus update/delete by non-owner.
5. Unauthorized nested bus resource mutation (photos/amenities/availability).
6. Production settings guard test (debug/ssl/hsts invariants).

---

## REFACTORING OPPORTUNITIES

**High Priority**
1. Extract payments into dedicated `apps/payments` module/service boundary.
2. Introduce booking/payment state machine with atomic transition helpers.
3. Centralize object-ownership permission classes for all ModelViewSets.

**Medium Priority**
1. Normalize endpoint-level request serializers for all mutating actions.
2. Standardize error-code response envelope for all exceptions.
3. Replace broad `except Exception` with explicit exception taxonomy.

---

## NEW FEATURES TO CONSIDER

1. **Payment idempotency keys**
   - Why: deterministic dedupe across retries/mobile flaky networks.
   - Implementation: require client-generated key + unique storage.

2. **Webhook replay protection**
   - Why: defend against delayed/replayed signed payloads.
   - Implementation: store event IDs + timestamp tolerance window.

3. **Atomic transition utility**
   - Why: eliminate repeated race-prone status code.
   - Implementation: helper performing lock + conditional transition + side effects.

4. **Security policy startup checks**
   - Why: prevent accidental insecure deployment.
   - Implementation: boot-time validation of production env flags.

5. **Audit trail enrichments**
   - Why: forensic clarity in payments and booking transitions.
   - Implementation: consistent correlation IDs on request/payment/webhook logs.

---

## POSITIVE HIGHLIGHTS

1. Strong use of `@transaction.atomic` in service layer.
2. Good separation of concerns: controllers are mostly thin and business logic in services.
3. Significant effort toward explicit error codes and documentation comments.
4. Signature verification and amount validation exist for Cashfree webhook path.
5. Query optimization (`select_related`/`prefetch_related`) is used in many list endpoints.

---

## ESTIMATED FIX TIME

| Priority | Issues | Dev Hours | Test Hours | Total |
|----------|--------|-----------|------------|-------|
| P0 | 4 | 14 | 10 | 24 |
| P1 | 8 | 18 | 12 | 30 |
| P2 | 10 | 14 | 8 | 22 |
| **Total** | **22** | **46** | **30** | **76h** |

---

## PRIORITY FIX ROADMAP

### Day 1 (CRITICAL - before any real traffic)
1. Bus object-authorization hardening (all update/delete paths).
2. Payment initiation lock + uniqueness constraints.
3. Booking completion lock-safe transition.

### Week 1 (BLOCKER - before onboarding users)
1. Payment confirmation/webhook lock-safe idempotency.
2. Error-code registry reconciliation (add undocumented 8 + map missing hot paths).
3. Add concurrency and security regression tests.

### Week 2 (HIGH - pre-scale)
1. Production security default hardening.
2. Remove broad catches on critical financial/auth flows.
3. Refactor payments to dedicated app boundary.

### Month 1 (MEDIUM)
1. Replay-protected webhook event store.
2. Booking/payment state machine abstraction.
3. Structured audit logging enhancements.

---

## FINAL VERDICT

**Launch Recommendation:** **BLOCK**

**Reasoning:** The current build has multiple exploitable authorization and race-condition defects in money and inventory paths. These are not cosmetic; they can alter listings, payment records, and counters under realistic concurrency.

**Conditions for Launch:**
1. **Must fix (P0):** authorization gaps in buses, payment initiation race, completion race, confirm/webhook race.
2. **Should fix (P1):** production security defaults, explicit error-code coverage for key failures.
3. **Monitor (P2):** architecture drift and observability normalization.

**Would This Pass:**
- Stripe-style code review? **NO** (idempotency + authorization gaps)
- Google production standards? **NO** (unsafe defaults + race-risk)
- SOC 2 audit? **NO** (control weaknesses in access + change integrity)
- PCI-DSS expectations? **PARTIAL/NO** (payment-path concurrency and ops hardening insufficient)

**Acquisition Due Diligence:**
> “Would MakeMyTrip’s CTO approve ₹1 crore acquisition after seeing this code?”  
**Answer:** **Not yet.** The architecture direction is promising, but critical control failures in authorization and transactional idempotency must be fixed first.

---

## APPENDIX: High-Value Regression Test Skeletons

```python
def test_bus_non_owner_cannot_patch():
    """Verify unauthorized bus mutation is blocked"""


def test_bus_non_owner_cannot_delete_availability_block():
    """Verify unauthorized inventory tampering is blocked"""


def test_payment_initiation_is_idempotent_under_parallel_requests():
    """Verify duplicate pending payments are prevented"""


def test_complete_booking_parallel_requests_single_side_effect():
    """Verify counters/history update once under race"""


def test_webhook_duplicate_delivery_single_transition():
    """Verify webhook replay does not duplicate payment state changes"""
```
