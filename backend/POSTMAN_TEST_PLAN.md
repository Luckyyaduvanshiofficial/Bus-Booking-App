# Postman Testing Plan - Bus Booking Platform
**Date:** February 14, 2026
**Focus:** Critical paths after 14-file bug fixes

---

## 🎯 Testing Priority (Execute in Order)

### Phase 1: Authentication & Setup (5 min)
- [ ] **Send OTP** - Verify rate limiting and notification
- [ ] **Verify OTP** - Check token generation
- [ ] **Register Customer** - Test user creation
- [ ] **Register Operator** - Test operator role
- [ ] **Admin Verify Operator** - Test verification flow

### Phase 2: Bus Creation & Management (5 min)
- [ ] **Create Bus (Operator)** - Test with various amenities
- [ ] **Upload Bus Photos** - Test image handling
- [ ] **Set Availability** - Test date blocking logic
- [ ] **List Buses** - Verify search and filters
- [ ] **Get Bus Details** - Check all nested data

### Phase 3: Booking Creation (CRITICAL - 10 min)
**Race Condition Tests:**
- [ ] **Create Booking (Customer)** - Single booking
- [ ] **Create Booking (Concurrent)** - Simulate 2 concurrent requests for same date
  - Expected: One succeeds, one gets `BOK-SERV-CONFLICT-001`
- [ ] **Create Booking with Return Date** - Multi-day blocking
- [ ] **Create Booking (Past Date)** - Should fail with `BOK-SERIAL-VAL-010`
- [ ] **Create Booking (Blocked Date)** - Should fail gracefully

**Pricing Tests:**
- [ ] **Create Booking (No Coupon)** - Verify base calculation
- [ ] **Create Booking (With Coupon)** - Verify discount applied
- [ ] **Create Booking (Expired Coupon)** - Should reject
- [ ] **Create Booking (Usage Limit Exceeded)** - Should reject

### Phase 4: Payment Flows (CRITICAL - 10 min)
**Financial Integrity Tests:**
- [ ] **Create Payment (Online Full)** - Test payment creation
- [ ] **Simulate Webhook (Success)** - Test signature verification
- [ ] **Simulate Webhook (Invalid Signature)** - Should reject with `PAY-VIEWS-AUTH-001`
- [ ] **Simulate Webhook (Amount Mismatch)** - Should fail with `PAY-SERV-VAL-001`
- [ ] **Create Payment (Partial)** - Test advance payment
- [ ] **Create Payment (Cash on Pickup)** - Test zero online amount
- [ ] **Get Payment Status** - Verify status tracking

### Phase 5: Operator Accept/Reject (CRITICAL - 10 min)
**State Transition Tests:**
- [ ] **Accept Booking (Operator)** - Verify status change to `accepted`
- [ ] **Accept Booking (Wrong Operator)** - Should fail with `BOK-VIEWS-PERM-002`
- [ ] **Accept Booking (Already Accepted)** - Should be idempotent
- [ ] **Reject Booking (Operator)** - Test rejection with reason
- [ ] **Reject Booking (After Payment)** - Verify refund triggered
- [ ] **Get Operator Bookings** - Check filtering by status

### Phase 6: Notification System (CRITICAL - 5 min)
**Notification Flow Tests:**
- [ ] **Create Booking** - Check if customer notification sent
- [ ] **Accept Booking** - Check if customer & operator notified
- [ ] **Reject Booking** - Check if customer notified
- [ ] **Payment Confirmed** - Check if operator notified
- [ ] **Mark Notification as Read** - Test read status
- [ ] **List Notifications (Customer)** - Verify unread count

### Phase 7: Review System (5 min)
- [ ] **Create Review (After Completion)** - Test review creation
- [ ] **Create Review (Before Completion)** - Should fail
- [ ] **Get Bus Reviews** - Verify rating aggregation
- [ ] **Update Review** - Test edit functionality

### Phase 8: Admin Operations (5 min)
- [ ] **List All Bookings (Admin)** - Test filtering
- [ ] **Verify Operator (Admin)** - Test document verification
- [ ] **View Operator Documents** - Check encryption
- [ ] **Platform Statistics** - Test aggregate queries

---

## 🔐 Critical Validations to Check

### Race Condition Fixes
- ✅ Bus locking with `select_for_update()` prevents double-booking
- ✅ Coupon usage counter incremented atomically
- ✅ Rating recalculation under lock

### Financial Integrity
- ✅ Amounts recalculated server-side (never trusted from client)
- ✅ Webhook signature verification
- ✅ Payment amount matches booking amount
- ✅ All money uses Decimal (not float)

### Notification System
- ✅ Customer notified on booking creation
- ✅ Operator notified on booking creation
- ✅ Customer notified on accept/reject
- ✅ Operator notified on payment
- ✅ Notifications use Brevo API

### Security
- ✅ Permissions checked (role + is_verified + is_active)
- ✅ No hardcoded secrets in responses
- ✅ Soft delete for financial records
- ✅ Error codes present on all errors

---

## 📊 Expected Results

### Success Criteria
- All auth flows complete without errors
- Booking creation prevents race conditions
- Payment webhooks verify signatures
- Operator actions check ownership
- Notifications delivered successfully
- Error codes match ERROR_REGISTRY.md

### Known Error Codes to Test
- `BOK-SERV-CONFLICT-001` - Bus unavailable
- `BOK-VIEWS-PERM-002` - Not booking owner
- `BOK-VIEWS-PERM-004` - Cannot delete paid booking
- `PAY-VIEWS-AUTH-001` - Invalid webhook signature
- `PAY-SERV-VAL-001` - Payment amount mismatch
- `BUS-VIEWS-PERM-003` - Operator not verified

---

## 🚀 Quick Test Commands

### Using Postman CLI (if available)
```bash
newman run postman_collection.json -e local.postman_environment.json
```

### Using curl (for quick tests)
```bash
# Send OTP
curl -X POST http://localhost:8000/api/v1/users/auth/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210"}'

# Create booking (test race condition)
curl -X POST http://localhost:8000/api/v1/bookings/bookings/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bus": 1, "pickup_date": "2026-03-01", "passenger_count": 2}'
```

---

## 📝 Test Results Log

| Test | Status | Time | Notes |
|------|--------|------|-------|
| Authentication Flow | ⏳ Pending | - | - |
| Booking Creation | ⏳ Pending | - | - |
| Payment Webhook | ⏳ Pending | - | - |
| Operator Actions | ⏳ Pending | - | - |
| Notifications | ⏳ Pending | - | - |

---

**Next Step:** Import `backend/postman_collection.json` into Postman and execute tests in order.
