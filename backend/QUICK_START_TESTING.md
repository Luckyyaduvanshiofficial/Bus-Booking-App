# 🚀 Quick Start Testing Guide - Bus Booking Platform

**Date:** February 14, 2026  
**Status:** ✅ Django Server Running on http://localhost:8000  
**Purpose:** Validate 14 recently fixed files for production readiness

---

## 📋 What Was Fixed (Priority Testing Areas)

### Critical Fixes to Validate:
1. **Race Condition Prevention** - `select_for_update()` in booking creation
2. **Payment Security** - HMAC webhook signature verification  
3. **Financial Integrity** - Server-side amount recalculation (Decimal)
4. **Notification System** - Brevo API integration
5. **Permission Checks** - Operator ownership verification
6. **Coupon Usage** - Atomic counter with F() expressions
7. **Rating Recalculation** - Lock-based aggregation
8. **Soft Delete** - Financial records never hard deleted
9. **Error Codes** - Structured error responses (ERROR_REGISTRY.md)
10. **Admin Actions** - Service layer for business logic

---

## 🎯 OPTION 1: Import Existing Postman Collection (RECOMMENDED)

### Steps:
1. **Open Postman Desktop App**

2. **Import Collection:**
   - Click "Import" button
   - Select file: `D:\Bus Booking app\backend\postman_collection.json`
   - Collection has **810 lines** with all endpoints pre-configured

3. **Set Base URL:**
   - Click on collection → Variables tab
   - Set `base_url` = `http://localhost:8000`

4. **Execute Test Sequence:**

   **Phase 1: Authentication (5 min)**
   ```
   → Send OTP (POST /api/v1/users/auth/send-otp/)
   → Verify OTP (POST /api/v1/users/auth/verify-otp/)
   → Register Customer (saves token automatically)
   → Register Operator (saves operator_token)
   ```

   **Phase 2: Bus Creation (5 min)**
   ```
   → Create Bus (POST /api/v1/buses/buses/)
     - Use operator_token
     - Expected: 403 if operator not verified (BUS-VIEWS-PERM-003)
     - Expected: 201 if verified (saves bus_id)
   ```

   **Phase 3: Booking Creation - CRITICAL RACE CONDITION TEST (10 min)**
   ```
   → Create Booking #1 (POST /api/v1/bookings/bookings/)
     {
       "bus": {{bus_id}},
       "pickup_date": "2026-03-15",
       "pickup_location": "Delhi",
       "drop_location": "Mumbai",
       "passenger_count": 2,
       "payment_mode": "online"
     }
     ✅ Expected: 201 Created (saves booking_id)

   → Create Booking #2 (SAME DATE, SAME BUS)
     {
       "bus": {{bus_id}},
       "pickup_date": "2026-03-15",  ← Same date!
       "pickup_location": "Delhi",
       "drop_location": "Jaipur",
       "passenger_count": 1,
       "payment_mode": "online"
     }
     ❌ Expected: 400 Bad Request
     ❌ Expected Error Code: BOK-SERV-CONFLICT-001
     ❌ Expected Message: "Bus is not available on: 2026-03-15"
     
     ✅ THIS VALIDATES THE select_for_update() FIX!
   ```

   **Phase 4: Payment Webhook - SECURITY TEST (10 min)**
   ```
   → Create Payment (POST /api/v1/bookings/payments/)
     {
       "booking": {{booking_id}},
       "amount": "1500.00",
       "payment_method": "card"
     }
     ✅ Expected: 201 Created (saves payment_id)

   → Webhook - Invalid Signature (POST /api/v1/bookings/webhooks/cashfree/)
     Headers:
       x-webhook-timestamp: 1234567890
       x-webhook-signature: invalid_signature_here
     Body:
       {
         "payment_id": "{{payment_id}}",
         "amount": 1500.00,
         "status": "captured"
       }
     ❌ Expected: 401 Unauthorized
     ❌ Expected Error Code: PAY-VIEWS-AUTH-001
     ❌ Expected Message: "Invalid signature"
     
     ✅ THIS VALIDATES THE HMAC VERIFICATION FIX!
   ```

   **Phase 5: Operator Actions - PERMISSION TEST (10 min)**
   ```
   → Accept Booking (POST /api/v1/bookings/bookings/{{booking_id}}/accept/)
     - Use operator_token
     - If operator owns bus: 200 OK
     - If operator doesn't own bus: 403 Forbidden (BOK-VIEWS-PERM-002)
     
     ✅ THIS VALIDATES THE PERMISSION CHECK FIX!

   → Reject Booking (POST /api/v1/bookings/bookings/{{booking_id}}/reject/)
     {
       "rejection_reason": "Bus maintenance scheduled"
     }
     - Same permission logic as Accept
   ```

   **Phase 6: Notifications (5 min)**
   ```
   → List Notifications (GET /api/v1/users/notifications/)
     - Use customer token
     - Check for booking creation notification
     - Check for accept/reject notifications
     
     ✅ THIS VALIDATES THE BREVO INTEGRATION FIX!
   ```

---

## 🎯 OPTION 2: Python Automated Test Runner

### Prerequisites:
```bash
# Ensure server is running
# http://localhost:8000 should be accessible
```

### Run Tests:
```powershell
cd "D:\Bus Booking app\backend"
& "D:/Bus Booking app/.venv/Scripts/Activate.ps1"
python run_postman_tests.py
```

### What It Tests:
- ✅ Authentication flow
- ✅ Booking creation (race condition)
- ✅ Payment flows
- ✅ Operator actions
- ✅ Notifications

### Output:
- Console: Real-time test results
- File: `postman_test_results.json` with detailed results

---

## 🎯 OPTION 3: Manual cURL Tests (Quick Validation)

### Test 1: Authentication
```bash
# Send OTP
curl -X POST http://localhost:8000/api/v1/users/auth/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210"}'

# Verify OTP (use code from console/email)
curl -X POST http://localhost:8000/api/v1/users/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "otp": "123456"}'

# Save the token from response
```

### Test 2: Race Condition (Most Critical)
```bash
# Create first booking
curl -X POST http://localhost:8000/api/v1/bookings/bookings/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "bus": 1,
    "pickup_date": "2026-03-15",
    "pickup_location": "Delhi",
    "drop_location": "Mumbai",
    "passenger_count": 2,
    "payment_mode": "online"
  }'

# Try to book SAME BUS, SAME DATE (should fail)
curl -X POST http://localhost:8000/api/v1/bookings/bookings/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "bus": 1,
    "pickup_date": "2026-03-15",
    "pickup_location": "Delhi",
    "drop_location": "Jaipur",
    "passenger_count": 1,
    "payment_mode": "online"
  }'

# Expected: {"detail": "Bus is not available on: 2026-03-15.", "code": "BOK-SERV-CONFLICT-001"}
```

---

## 📊 Success Criteria

### ✅ Tests Must Pass:
- [ ] Authentication flow completes without errors
- [ ] Duplicate booking rejected with `BOK-SERV-CONFLICT-001`
- [ ] Webhook with invalid signature rejected with `PAY-VIEWS-AUTH-001`
- [ ] Non-owner operator blocked with `BOK-VIEWS-PERM-002`
- [ ] Notifications delivered (check Brevo dashboard or console logs)
- [ ] All error codes match ERROR_REGISTRY.md

### ✅ Expected Error Codes to See:
- `BOK-SERV-CONFLICT-001` - Bus unavailable (race condition prevented)
- `BOK-VIEWS-PERM-002` - Not booking owner
- `BOK-VIEWS-PERM-004` - Cannot delete paid booking
- `PAY-VIEWS-AUTH-001` - Invalid webhook signature
- `PAY-SERV-VAL-001` - Payment amount mismatch
- `BUS-VIEWS-PERM-003` - Operator not verified

---

## 🔍 What to Look For

### In Django Server Logs:
```
INFO - Booking created: ID=123
INFO - Notification sent via Brevo: booking_created
INFO - Payment webhook received (signature valid)
WARNING - Invalid webhook signature attempt from IP=127.0.0.1
```

### In Brevo Dashboard (if configured):
- Check "Transactional > Logs"
- Look for emails sent to test phone/email
- Verify templates: `booking_created`, `booking_accepted`, `booking_rejected`

### In Database (Optional):
```sql
-- Check booking was created
SELECT * FROM bookings_booking WHERE id = 1;

-- Check availability block was created
SELECT * FROM buses_availabilityblock WHERE bus_id = 1 AND blocked_date = '2026-03-15';

-- Check notification was created
SELECT * FROM users_notification WHERE user_id = 1 ORDER BY created_at DESC;

-- Check payment was created
SELECT * FROM bookings_payment WHERE booking_id = 1;
```

---

## 🚨 Troubleshooting

### Issue: Can't send OTP
- **Check:** Brevo API key configured in `.env`
- **Check:** Phone number format: `+91XXXXXXXXXX`
- **Workaround:** Use test OTP `123456` if in dev mode

### Issue: 403 on Create Bus
- **Cause:** Operator not verified
- **Solution:** As admin, verify operator:
  ```
  POST /api/v1/users/users/{operator_id}/verify/
  Authorization: Token {admin_token}
  ```

### Issue: Booking doesn't fail on duplicate date
- **Problem:** Race condition fix not working
- **Check:** Ensure `select_for_update()` is in `BookingService.create_booking()`
- **Check:** Database supports row-level locking (PostgreSQL)

### Issue: Webhook always fails
- **Check:** Signature calculation in `views.py`
- **Check:** `CASHFREE_SECRET_KEY` environment variable
- **Note:** For testing, you can temporarily disable signature check (NOT FOR PRODUCTION)

---

## 📝 Test Results Template

| Test | Status | Error Code | Notes |
|------|--------|-----------|-------|
| Send OTP | ⏳ | - | - |
| Verify OTP | ⏳ | - | - |
| Register Customer | ⏳ | - | - |
| Register Operator | ⏳ | - | - |
| Create Bus | ⏳ | - | - |
| Create Booking #1 | ⏳ | - | - |
| Create Booking #2 (duplicate) | ⏳ | BOK-SERV-CONFLICT-001 | Should fail ❌ |
| Create Payment | ⏳ | - | - |
| Webhook (invalid sig) | ⏳ | PAY-VIEWS-AUTH-001 | Should fail ❌ |
| Accept Booking | ⏳ | - | - |
| Reject Booking | ⏳ | - | - |
| List Notifications | ⏳ | - | - |

---

## 🎉 Next Steps After Testing

1. **If All Tests Pass:**
   - Mark files as production-ready ✅
   - Proceed to frontend testing
   - Deploy to staging environment

2. **If Tests Fail:**
   - Check ERROR_REGISTRY.md for error code details
   - Review service layer logic
   - Check logs for stack traces
   - Re-run specific failing test

3. **For TestSprite Automated Tests:**
   - Create API key: https://www.testsprite.com/dashboard/settings/apikey
   - Run: `mcp_testsprite_testsprite_generate_backend_test_plan`
   - Generate comprehensive test coverage

---

**Ready to test?** Start with Option 1 (Postman Collection Import) for the most comprehensive experience! 🚀
