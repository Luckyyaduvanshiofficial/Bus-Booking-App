# Code Review Kickoff Plan

This document starts the code review workflow for the Bus Booking App and translates the current audit report into an actionable execution sequence.

## Objective

Run a focused, risk-first review to move the project from **BLOCK** to a releasable state by fixing and validating critical authorization and concurrency issues first.

## Review Scope

- Backend APIs and service-layer state transitions (`backend/apps/**`)
- Security-sensitive settings (`backend/bus_booking/settings.py`)
- Regression coverage for authorization, race conditions, and payment idempotency

## Priority Queue

1. **P0 Authorization controls**
   - Validate object-level ownership checks in all bus-related mutation endpoints.
   - Add and verify explicit negative tests for cross-account actions.

2. **P0 Payment initiation idempotency**
   - Add transactional locking + uniqueness guarantees for pending payments.
   - Verify behavior under concurrent requests.

3. **P0 Booking completion race safety**
   - Guard transitions with lock-first strategy.
   - Ensure counters and history are incremented exactly once.

4. **P0/P1 Payment confirmation race handling**
   - Enforce atomic status transition and replay-safe confirmation handling.
   - Verify duplicate webhook delivery remains idempotent.

5. **P1 Production hardening defaults**
   - Enforce secure defaults in production mode.
   - Add startup/runtime checks for unsafe production configuration.

## Execution Workflow

1. Triage and assign one owner per critical item.
2. Reproduce each issue with focused tests (expected failing state).
3. Implement minimal, high-confidence fix.
4. Re-run targeted tests + full suite.
5. Document residual risk and rollout notes.

## Exit Criteria (for "Review Started" status)

A review cycle is considered started when all below are complete:

- [x] Risk-prioritized issue queue documented.
- [x] Scope and execution workflow documented.
- [ ] Owner assignment completed for each P0 item.
- [ ] Reproduction tests added for each P0 item.
- [ ] First P0 patch opened with regression tests.

## Suggested Verification Commands

```bash
# backend tests
cd backend && python manage.py test

# quick static sanity
python -m compileall backend/apps

# optional: run focused tests once created
cd backend && python manage.py test apps.bookings apps.buses
```
