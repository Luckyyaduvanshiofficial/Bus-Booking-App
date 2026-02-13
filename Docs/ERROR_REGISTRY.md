# ERROR REGISTRY - Bus Booking Platform

**Purpose:** Central registry of all error codes in the system  
**Usage:** When error occurs, search this file by error code to find source + solution  
**Last Updated:** 2026-02-13

---

## 📋 TABLE OF CONTENTS

1. [Error Code Format](#error-code-format)
2. [Users App Errors (USR-*)](#users-app-errors)
3. [Buses App Errors (BUS-*)](#buses-app-errors)
4. [Bookings App Errors (BOK-*)](#bookings-app-errors)
5. [Payments App Errors (PAY-*)](#payments-app-errors)
6. [Reviews App Errors (REV-*)](#reviews-app-errors)
7. [Documents App Errors (DOC-*)](#documents-app-errors)
8. [Common Errors (COM-*)](#common-errors)

---

## ERROR CODE FORMAT

```
[APP]-[FILE]-[TYPE]-[NUMBER]

APP:
- USR = Users app
- BUS = Buses app
- BOK = Bookings app
- PAY = Payments app
- REV = Reviews app
- DOC = Documents app
- COM = Common/shared code

FILE:
- MODELS = models.py
- VIEWS = views.py
- SERV = services.py
- SERIAL = serializers.py
- ADMIN = admin.py
- UTILS = utils.py
- MW = middleware.py

TYPE:
- VAL = Validation error
- PERM = Permission denied
- DB = Database error
- API = External API error
- AUTH = Authentication error
- NOTFOUND = Object not found
- CONFLICT = Business logic conflict
- CONFIG = Configuration/setup error

NUMBER:
- 001, 002, 003... (sequential within each file)
```

---

## USERS APP ERRORS

### USR-MODELS-* (apps/users/models.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| USR-MODELS-VAL-001 | "Phone number must be 10 digits" | Invalid phone format | Check phone_number field validation |
| USR-MODELS-VAL-002 | "Invalid user role. Must be: customer, operator, or admin" | Role field has invalid value | Check User.Role.choices |
| USR-MODELS-VAL-003 | "Email already exists" | Duplicate email in database | Check User.email unique constraint |
| USR-MODELS-DB-001 | "Failed to save user to database" | Database connection/constraint issue | Check database connection, run migrations |
| USR-MODELS-CONFLICT-001 | "Cannot delete user with active bookings" | User has related bookings | Cancel bookings first or use soft delete |

### USR-VIEWS-* (apps/users/views.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| USR-VIEWS-AUTH-001 | "Authentication required" | No auth token provided | Check Authorization header |
| USR-VIEWS-AUTH-002 | "Invalid or expired token" | Token is malformed/expired | Re-login to get new token |
| USR-VIEWS-PERM-001 | "Only operators can access this endpoint" | User role is not 'operator' | Check user.role in request |
| USR-VIEWS-PERM-002 | "Only admins can approve operators" | User role is not 'admin' | Admin-only action attempted |
| USR-VIEWS-NOTFOUND-001 | "User not found" | User ID doesn't exist | Check user_id in request |
| USR-VIEWS-VAL-001 | "Password must be at least 8 characters" | Weak password | Enforce password requirements |

### USR-SERV-* (apps/users/services.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| USR-SERV-AUTH-001 | "Invalid phone/OTP combination" | OTP verification failed | Check Supabase Auth logs |
| USR-SERV-AUTH-002 | "OTP expired. Please request new one" | OTP timeout exceeded | Request new OTP |
| USR-SERV-CONFLICT-001 | "Operator already verified" | Attempting to re-verify | Check operator.is_verified status |
| USR-SERV-VAL-001 | "Profile incomplete. Add city and address" | Required fields missing | Complete profile before operator registration |

### USR-SERIAL-* (apps/users/serializers.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| USR-SERIAL-VAL-001 | "Phone must contain only digits" | Phone has letters/special chars | Provide digits-only phone number |
| USR-SERIAL-VAL-002 | "Phone must be 10-15 digits" | Phone number length invalid | Provide 10-15 digit phone number |
| USR-SERIAL-VAL-003 | "Role must be customer or operator" | Invalid registration role | Set role to 'customer' or 'operator' |

---

## BUSES APP ERRORS

### BUS-MODELS-* (apps/buses/models.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| BUS-MODELS-VAL-001 | "Bus name required (max 200 characters)" | Empty or too long name | Check Bus.name field |
| BUS-MODELS-VAL-002 | "Capacity must be between 10 and 60 seats" | Invalid capacity value | Check MinValueValidator(10), MaxValueValidator(60) |
| BUS-MODELS-VAL-003 | "Base price must be positive" | Negative price entered | Check BusPricing.base_price >= 0 |
| BUS-MODELS-VAL-004 | "At least one operating city required" | Empty operating_cities list | Add cities to Bus.operating_cities |
| BUS-MODELS-CONFLICT-001 | "Cannot delete bus with future bookings" | Bus has upcoming bookings | Cancel bookings or soft delete bus |
| BUS-MODELS-DB-001 | "Failed to save bus photos" | Cloudinary upload failed | Check Cloudinary config, retry upload |

### BUS-VIEWS-* (apps/buses/views.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| BUS-VIEWS-PERM-001 | "Only operators can create buses" | Non-operator tried to create | Check user.role == 'operator' |
| BUS-VIEWS-PERM-002 | "You can only edit your own buses" | Operator editing another's bus | Check bus.operator == request.user |
| BUS-VIEWS-NOTFOUND-001 | "Bus not found" | Invalid bus_id | Check bus exists, not deleted |
| BUS-VIEWS-VAL-001 | "At least 3 photos required" | Less than 3 photos uploaded | Upload minimum 3 bus photos |
| BUS-VIEWS-VAL-002 | "Image file too large (max 5MB)" | Photo exceeds size limit | Compress image before upload |
| BUS-VIEWS-VAL-003 | "Invalid image format. Use JPG/PNG" | Unsupported file type | Convert to JPEG or PNG |

### BUS-SERV-* (apps/buses/services.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| BUS-SERV-VAL-001 | "Search requires: from_city, to_city, date, capacity" | Missing search parameters | Provide all required fields |
| BUS-SERV-NOTFOUND-001 | "No buses available for selected criteria" | No matching buses | Try different date/route |
| BUS-SERV-CONFLICT-001 | "Bus already blocked on this date" | Duplicate availability block | Check existing blocks before creating |
| BUS-SERV-DB-001 | "Failed to calculate distance between cities" | Geocoding API failed | Check network, API quota |
| BUS-SERV-CONFIG-001 | "Operating cities list is empty" | City configuration missing | Add cities to settings.OPERATING_CITIES |

### BUS-SERIAL-* (apps/buses/serializers.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| BUS-SERIAL-VAL-001 | "Seating capacity must be at least 1" | Value is less than 1 | Set seating_capacity >= 1 |
| BUS-SERIAL-VAL-002 | "Seating capacity cannot exceed 100" | Value exceeds 100 | Set seating_capacity <= 100 |
| BUS-SERIAL-VAL-003 | "Price per km must be positive" | Zero or negative price | Set positive price_per_km |
| BUS-SERIAL-VAL-004 | "Base price cannot be negative" | Negative base_price | Set base_price >= 0 |

---

## BOOKINGS APP ERRORS

### BOK-MODELS-* (apps/bookings/models.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| BOK-MODELS-VAL-001 | "Pickup datetime must be in future" | Past date selected | Choose future date |
| BOK-MODELS-VAL-002 | "Return date must be after pickup date" | Invalid date range | Fix date order |
| BOK-MODELS-VAL-003 | "Passenger count exceeds bus capacity" | Too many passengers | Choose bigger bus or reduce passengers |
| BOK-MODELS-VAL-004 | "Total amount must be positive" | Invalid pricing calculation | Check pricing logic |
| BOK-MODELS-CONFLICT-001 | "Cannot modify confirmed booking" | Trying to edit locked booking | Only pending bookings can be modified |
| BOK-MODELS-CONFLICT-002 | "Cannot cancel paid booking directly" | Payment already processed | Initiate refund first |

### BOK-VIEWS-* (apps/bookings/views.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| BOK-VIEWS-PERM-001 | "Only customers can create bookings" | Non-customer tried to book | Check user.role == 'customer' |
| BOK-VIEWS-PERM-002 | "Only operator can accept/reject bookings" | Customer tried operator action | Check user.role == 'operator' |
| BOK-VIEWS-PERM-003 | "You can only view your own bookings" | Accessing another user's booking | Check booking ownership |
| BOK-VIEWS-NOTFOUND-001 | "Booking not found" | Invalid booking_id | Check booking exists |
| BOK-VIEWS-VAL-001 | "Booking must be in pending status to cancel" | Wrong status transition | Check booking.status |
| BOK-VIEWS-CONFLICT-001 | "Bus already booked for this date" | Double booking attempt | Bus not available |

### BOK-SERV-* (apps/bookings/services.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| BOK-SERV-CONFLICT-001 | "Bus not available on selected date" | Availability block exists | Choose different date |
| BOK-SERV-CONFLICT-002 | "Operator has insufficient wallet balance" | Commission can't be deducted | Operator must top up wallet |
| BOK-SERV-DB-001 | "Failed to create booking and block availability" | Transaction rollback | Check database constraints |
| BOK-SERV-DB-002 | "Race condition detected. Please retry" | Concurrent booking attempt | Retry booking |
| BOK-SERV-VAL-001 | "Pricing calculation failed" | Invalid pricing data | Check BusPricing model |
| BOK-SERV-API-001 | "Failed to send booking confirmation SMS" | SMS API error | Check MSG91 logs, retry |
| BOK-SERV-CONFLICT-003 | "Cannot reveal contact before 2 hours of trip" | Early contact reveal attempt | Wait until 2 hours before pickup |

### BOK-SERIAL-* (apps/bookings/serializers.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| BOK-SERIAL-VAL-001 | "This bus is no longer active" | Bus deactivated | Choose a different active bus |
| BOK-SERIAL-VAL-002 | "This bus has not been approved yet" | Bus pending approval | Choose an approved bus |
| BOK-SERIAL-VAL-003 | "Passenger count exceeds bus capacity" | Too many passengers | Choose larger bus or reduce passengers |
| BOK-SERIAL-VAL-004 | "Return date cannot be before pickup date" | Invalid date range | Set return_date after pickup_date |
| BOK-SERIAL-VAL-005 | "Return date required for round trips" | Round trip missing return_date | Provide return_date |
| BOK-SERIAL-VAL-006 | "Passenger count must be at least 1" | Zero passengers | Set passenger_count >= 1 |
| BOK-SERIAL-VAL-007 | "Invalid status value for respond action" | Status must be 'confirmed' or 'rejected' | Pass status='confirmed' or status='rejected' |

---

## PAYMENTS APP ERRORS

### PAY-MODELS-* (apps/payments/models.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| PAY-MODELS-VAL-001 | "Payment amount must match booking amount" | Mismatch detected | Check calculation logic |
| PAY-MODELS-VAL-002 | "Payment method required (online/cash)" | Missing payment_method | Provide payment method |
| PAY-MODELS-CONFLICT-001 | "Payment already processed for this booking" | Duplicate payment attempt | Check payment.status |
| PAY-MODELS-CONFLICT-002 | "Cannot refund unpaid booking" | Refund on pending payment | Check payment status first |

### PAY-VIEWS-* (apps/payments/views.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| PAY-VIEWS-PERM-001 | "Only booking owner can make payment" | Unauthorized payment attempt | Check booking.customer == user |
| PAY-VIEWS-NOTFOUND-001 | "Payment not found" | Invalid payment_id | Check payment exists |
| PAY-VIEWS-VAL-001 | "Cashfree order creation failed" | API error | Check Cashfree logs |
| PAY-VIEWS-VAL-002 | "Booking must be confirmed before payment" | Booking status is not 'confirmed' | Wait for operator to confirm the booking first |
| PAY-VIEWS-CONFLICT-001 | "Booking already paid" | Duplicate payment | Check booking.payment_status |

### PAY-SERV-* (apps/payments/services.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| PAY-SERV-API-001 | "Cashfree API error: [details]" | External API failure | Check Cashfree status page |
| PAY-SERV-API-002 | "Payment webhook signature invalid" | Tampered webhook | Check webhook secret |
| PAY-SERV-CONFLICT-001 | "Payment status mismatch" | Status sync issue | Verify with Cashfree API |
| PAY-SERV-DB-001 | "Failed to update payment status" | Database error | Check transaction logs |
| PAY-SERV-CONFIG-001 | "Cashfree credentials missing" | Env vars not set | Set CASHFREE_APP_ID, CASHFREE_SECRET_KEY |
| PAY-SERV-VAL-001 | "Refund amount exceeds original payment" | Invalid refund amount | Check refund calculation |

---

## REVIEWS APP ERRORS

### REV-MODELS-* (apps/reviews/models.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| REV-MODELS-VAL-001 | "Rating must be between 1 and 5" | Invalid rating value | Check rating field validation |
| REV-MODELS-VAL-002 | "Review comment required (min 10 characters)" | Too short comment | Write meaningful review |
| REV-MODELS-CONFLICT-001 | "Cannot review booking before completion" | Early review attempt | Wait until trip ends |
| REV-MODELS-CONFLICT-002 | "Review already submitted for this booking" | Duplicate review | One review per booking allowed |

### REV-VIEWS-* (apps/reviews/views.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| REV-VIEWS-PERM-001 | "Only booking customer can leave review" | Unauthorized review | Check booking.customer == user |
| REV-VIEWS-PERM-002 | "Only admins can moderate reviews" | Non-admin moderation attempt | Admin-only action |
| REV-VIEWS-NOTFOUND-001 | "Review not found" | Invalid review_id | Check review exists |
| REV-VIEWS-VAL-001 | "Cannot review cancelled booking" | Booking was cancelled | Only completed bookings reviewable |

### REV-SERV-* (apps/reviews/services.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| REV-SERV-VAL-001 | "Review contains profanity" | Bad language detected | Rephrase review |
| REV-SERV-CONFLICT-001 | "Booking must be completed before review" | Status check failed | Wait for booking completion |
| REV-SERV-DB-001 | "Failed to update bus average rating" | Aggregate calculation error | Recalculate manually |

### REV-SERIAL-* (apps/reviews/serializers.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| REV-SERIAL-VAL-001 | "You can only review your own bookings" | User is not booking customer | Only review your own bookings |
| REV-SERIAL-VAL-002 | "Only completed bookings can be reviewed" | Booking not completed | Wait for trip completion |
| REV-SERIAL-VAL-003 | "This booking already has a review" | Duplicate review | One review per booking |
| REV-SERIAL-VAL-004 | "Rating must be between 1 and 5" | Sub-rating out of range | Provide 1-5 rating |

---

## DOCUMENTS APP ERRORS

### DOC-MODELS-* (apps/documents/models.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| DOC-MODELS-VAL-001 | "Document type required (permit/fitness/insurance/rc)" | Missing doc_type | Specify document type |
| DOC-MODELS-VAL-002 | "Expiry date must be in future" | Expired document uploaded | Upload valid document |
| DOC-MODELS-VAL-003 | "Document file required" | No file uploaded | Upload PDF/image file |
| DOC-MODELS-CONFLICT-001 | "Document already uploaded for this bus" | Duplicate document | Update existing instead |

### DOC-VIEWS-* (apps/documents/views.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| DOC-VIEWS-PERM-001 | "Only bus operator can upload documents" | Unauthorized upload | Check bus ownership |
| DOC-VIEWS-PERM-002 | "Only admins can approve/reject documents" | Non-admin verification | Admin-only action |
| DOC-VIEWS-NOTFOUND-001 | "Document not found" | Invalid document_id | Check document exists |
| DOC-VIEWS-VAL-001 | "File size exceeds 10MB limit" | Large file upload | Compress PDF/image |
| DOC-VIEWS-VAL-002 | "Invalid file type. Use PDF or JPG/PNG" | Wrong file format | Convert to supported format |

### DOC-SERV-* (apps/documents/services.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| DOC-SERV-API-001 | "OCR extraction failed" | Azure AI error | Check Azure credits, retry |
| DOC-SERV-API-002 | "Cloudinary upload failed" | Storage API error | Check Cloudinary quota |
| DOC-SERV-VAL-001 | "Document verification failed: [reason]" | OCR/validation issue | Manual review needed |
| DOC-SERV-CONFIG-001 | "Azure AI credentials missing" | Env vars not set | Set AZURE_AI_ENDPOINT, AZURE_AI_KEY |
| DOC-SERV-DB-001 | "Failed to update document status" | Database error | Check transaction |

---

## COMMON ERRORS

### COM-UTILS-* (utils/*.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| COM-UTILS-API-001 | "n8n webhook trigger failed" | n8n unreachable | Check n8n status, network |
| COM-UTILS-API-002 | "SMS send failed via MSG91" | SMS API error | Check MSG91 credits, logs |
| COM-UTILS-API-003 | "Cloudinary image upload failed" | Storage error | Check quota, retry |
| COM-UTILS-CONFIG-001 | "Environment variable [VAR_NAME] missing" | Missing config | Set in .env file |
| COM-UTILS-VAL-001 | "Invalid date format. Use YYYY-MM-DD" | Date parsing error | Check date string format |
| COM-UTILS-VAL-002 | "Invalid phone number format" | Phone validation failed | Use +91XXXXXXXXXX format |
| COM-UTILS-DB-001 | "Database connection lost" | Network/DB issue | Check Supabase connection |
| COM-UTILS-DB-002 | "Query timeout (>30s)" | Slow query | Optimize query, add indexes |

### COM-MIDDLEWARE-* (middleware.py)

| Code | Error Message | Cause | Solution |
|------|--------------|-------|----------|
| COM-MW-AUTH-001 | "Supabase Auth token invalid" | Bad token | Re-authenticate |
| COM-MW-AUTH-002 | "Token expired" | Session timeout | Login again |
| COM-MW-PERM-001 | "CORS error: Origin not allowed" | CORS configuration | Add origin to ALLOWED_HOSTS |
| COM-MW-RATE-001 | "Rate limit exceeded. Try again in [X] seconds" | Too many requests | Implement backoff |

---

## HOW TO USE THIS REGISTRY

### When Error Occurs in Development:

1. **Check Error Code in Log**
   ```
   Error: BUS-SERV-CONFLICT-001: Bus already blocked on this date
   ```

2. **Search This File**
   - Use Ctrl+F to find `BUS-SERV-CONFLICT-001`

3. **Read Error Details**
   - Cause: Duplicate availability block
   - Solution: Check existing blocks before creating

4. **Go to Source File**
   - File: `apps/buses/services.py`
   - Search for `BUS-SERV-CONFLICT-001` in comments

5. **Fix the Bug**

### When Error Occurs in Production:

1. **User Reports:** "I can't book a bus"

2. **Check Logs:**
   ```
   [2026-02-13 10:45:23] ERROR: BOK-SERV-CONFLICT-001
   Message: Bus not available on selected date
   User: customer_123
   Bus: bus_456
   Date: 2026-03-01
   ```

3. **Search Registry:** Find `BOK-SERV-CONFLICT-001`

4. **Debug:**
   - Go to `apps/bookings/services.py`
   - Look for availability check logic
   - Find why bus shows as unavailable

5. **Fix & Deploy**

---

## ADDING NEW ERROR CODES

When adding new code to project:

1. **Choose Next Available Number**
   - Check last number in relevant section
   - Increment by 1

2. **Add to Registry**
   ```markdown
   | BUS-SERV-VAL-005 | "New error message" | Cause | Solution |
   ```

3. **Add to Code**
   ```python
   # apps/buses/services.py
   
   # Error Code: BUS-SERV-VAL-005
   # Message: New error message
   # Cause: Explanation of what triggers this
   # Solution: How to fix it
   if some_condition:
       raise ValidationError(
           "New error message",
           code='BUS-SERV-VAL-005'
       )
   ```

4. **Commit Both**
   - Registry update + code change in same commit

---

## ERROR CODE STATISTICS

**Total Error Codes Defined:** 121

**By App:**
- Users: 18 codes (15 original + 3 SERIAL)
- Buses: 21 codes (17 original + 4 SERIAL)
- Bookings: 26 codes (19 original + 7 SERIAL)
- Payments: 15 codes
- Reviews: 15 codes (11 original + 4 SERIAL)
- Documents: 14 codes
- Common: 12 codes

**By Type:**
- VAL (Validation): 35%
- PERM (Permission): 15%
- CONFLICT (Business Logic): 20%
- API (External): 12%
- DB (Database): 10%
- NOTFOUND: 5%
- AUTH: 3%

---

## RELATED FILES

- `apps/*/models.py` - Model validation errors
- `apps/*/views.py` - View/permission errors
- `apps/*/services.py` - Business logic errors
- `utils/exceptions.py` - Custom exception classes
- `config/logging.py` - Logging configuration

---

**Last Updated:** 2026-02-13  
**Maintainer:** Development Team  
**Review Frequency:** Add new codes as features are built
