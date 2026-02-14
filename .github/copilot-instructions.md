# Copilot Instructions - Bus Booking Platform (FAANG-Level)

**Project:** Django + Next.js Financial Platform  
**Standards:** Google L6/Meta E6/Stripe Staff Engineer Level  
**Zero Tolerance:** Security, Race Conditions, Financial Integrity

---

## 🎯 CORE PRINCIPLE: DEFENSE IN DEPTH

**Every layer validates. Never trust anything.**

- Client validates → Serializer validates → Service validates → Model validates
- Every user input is hostile until proven otherwise
- Every external API call can fail
- Every database operation can race
- Every permission must be checked twice

**Quality Gate:** "Would this survive a Stripe security audit?"

---

## 🔐 SECURITY-FIRST RULES (NON-NEGOTIABLE)

### Rule 1: Secrets & Configuration
```python
# ❌ NEVER - Fallback to insecure defaults
SECRET_KEY = config('SECRET_KEY', default='dev-key-12345')

# ✅ ALWAYS - Fail fast if missing
SECRET_KEY = config('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY environment variable required')

# ❌ NEVER - Hardcoded credentials
CASHFREE_SECRET = 'sk_test_abc123'

# ✅ ALWAYS - Environment only
CASHFREE_SECRET = config('CASHFREE_SECRET')

# ❌ NEVER - Conditionally secure
DB_SSL = config('DB_SSLMODE', default='prefer')

# ✅ ALWAYS - Secure by default
IS_PRODUCTION = not DEBUG
DB_SSL = config('DB_SSLMODE', default='require' if IS_PRODUCTION else 'disable')
```

**Rationale:** Google/Meta principle - secure defaults, no silent failures.

---

### Rule 2: Authentication & Authorization
```python
# ❌ NEVER - Single check
if user.role == 'operator':
    create_bus()

# ✅ ALWAYS - Verify role + status
if user.role != CustomUser.Role.OPERATOR:
    # Error Code: BUS-VIEWS-PERM-001
    raise PermissionDenied('Only operators can create buses', code='BUS-VIEWS-PERM-001')

if not user.is_verified:
    # Error Code: BUS-VIEWS-PERM-003  
    raise PermissionDenied('Operator must be verified', code='BUS-VIEWS-PERM-003')

if not user.is_active:
    # Error Code: USR-VIEWS-PERM-004
    raise PermissionDenied('Account is disabled', code='USR-VIEWS-PERM-004')

# ❌ NEVER - Trust permissions once
class ViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOperator]

# ✅ ALWAYS - Verify ownership in every method
def update(self, request, pk=None):
    obj = self.get_object()
    if obj.owner != request.user:
        # Error Code: [APP]-VIEWS-PERM-002
        raise PermissionDenied('Can only edit own resources', code='...')
```

**Rationale:** Stripe principle - verify at every boundary, never cache permissions.

---

### Rule 3: Data Encryption at Rest
```python
# ❌ NEVER - Store sensitive data plaintext
class User(models.Model):
    bank_account = models.CharField(max_length=20)
    pan_number = models.CharField(max_length=10)

# ✅ ALWAYS - Encrypt before save, decrypt on read
from cryptography.fernet import Fernet
from django.conf import settings

class User(models.Model):
    _bank_account_encrypted = models.TextField(db_column='bank_account')
    _pan_number_encrypted = models.TextField(db_column='pan_number')
    
    @property
    def bank_account(self):
        return self._decrypt(self._bank_account_encrypted)
    
    @bank_account.setter
    def bank_account(self, value):
        self._bank_account_encrypted = self._encrypt(value)
    
    def _encrypt(self, value):
        if not value:
            return None
        f = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        return f.encrypt(value.encode()).decode()
    
    def _decrypt(self, value):
        if not value:
            return None
        f = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        return f.decrypt(value.encode()).decode()
```

**Rationale:** Meta/Google mandate - PII encrypted at rest, not just in transit.

---

### Rule 4: Admin Actions Use Service Layer
```python
# ❌ NEVER - Bulk update bypasses business logic
@admin.action(description='Approve operators')
def approve_operators(modeladmin, request, queryset):
    queryset.update(is_verified=True)  # Skips validation, signals, audit

# ✅ ALWAYS - Call service method per record
@admin.action(description='Approve operators')
def approve_operators(modeladmin, request, queryset):
    for user in queryset.filter(role=CustomUser.Role.OPERATOR):
        try:
            UserService.verify_user(user=user, action='approve', verified_by=request.user)
            # Creates notification, audit log, sends email
        except ValidationError as e:
            messages.error(request, f'{user}: {e}')
```

**Rationale:** Amazon principle - admin UI is just another client, same rules apply.

---

## ⚡ RACE CONDITION PREVENTION (CRITICAL FOR MONEY)

### Rule 5: Lock Before Check-Then-Act
```python
# ❌ NEVER - Check availability without lock
@transaction.atomic
def create_booking(bus_id, date):
    bus = Bus.objects.get(id=bus_id)
    if bus.is_available_on(date):  # Race window here!
        AvailabilityBlock.objects.create(bus=bus, date=date)

# ✅ ALWAYS - Lock row before check
@transaction.atomic
def create_booking(bus_id, date):
    # Step 1: Acquire exclusive row lock
    # Blocks concurrent transactions until we commit
    bus = Bus.objects.select_for_update().get(id=bus_id)
    
    # Step 2: Now safe to check (others are waiting)
    if not bus.is_available_on(date):
        # Error Code: BOK-SERV-CONFLICT-001
        raise ValidationError('Bus unavailable', code='BOK-SERV-CONFLICT-001')
    
    # Step 3: Create block (still locked)
    AvailabilityBlock.objects.create(bus=bus, date=date)
    # Lock released on transaction commit
```

**Why:** PostgreSQL `SELECT FOR UPDATE` prevents:
- Lost updates (two writes overwrite each other)
- Phantom reads (row appears/disappears mid-transaction)
- Double-booking (both see available, both book)

---

### Rule 6: Lock Shared Resources in Counters
```python
# ❌ NEVER - Increment without lock
coupon.used_count += 1
coupon.save()

# ✅ ALWAYS - Lock + revalidate + atomic update
with transaction.atomic():
    # Lock coupon row
    coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)
    
    # Revalidate (state might have changed while waiting for lock)
    if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
        # Error Code: BOK-SERV-CONFLICT-004
        raise ValidationError('Coupon exhausted', code='BOK-SERV-CONFLICT-004')
    
    # Atomic increment (F() uses UPDATE SET used_count = used_count + 1)
    Coupon.objects.filter(pk=coupon.pk).update(used_count=F('used_count') + 1)
```

**Rationale:** Stripe payment systems - counters must be atomic or money disappears.

---

### Rule 7: Lock During Aggregate Recalculation
```python
# ❌ NEVER - Calculate rating without lock
def update_bus_rating(bus_id):
    reviews = BusReview.objects.filter(bus_id=bus_id)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    Bus.objects.filter(id=bus_id).update(rating_avg=avg_rating)

# ✅ ALWAYS - Lock target row during recalc
with transaction.atomic():
    # Lock bus row (prevents concurrent rating updates)
    bus = Bus.objects.select_for_update().get(pk=bus_id)
    
    # Calculate fresh (concurrent reviews might have been added)
    aggregates = BusReview.objects.filter(bus=bus).aggregate(
        avg=Avg('rating_overall'),
        count=Count('id')
    )
    
    # Update atomically
    bus.rating_avg = round(aggregates['avg'] or 0, 1)
    bus.rating_count = aggregates['count'] or 0
    bus.save(update_fields=['rating_avg', 'rating_count', 'updated_at'])
```

**Rationale:** Google Maps ratings - prevent rating flicker from concurrent updates.

---

## 💰 FINANCIAL INTEGRITY (ZERO TOLERANCE)

### Rule 8: Recalculate Money Server-Side
```python
# ❌ NEVER - Trust client-provided amounts
@api_view(['POST'])
def create_booking(request):
    total = request.data['total_amount']  # Client says ₹10,000
    Booking.objects.create(total_amount=total)  # We believe them!

# ✅ ALWAYS - Calculate server-side, compare client value
@transaction.atomic
def create_booking(*, validated_data, customer):
    bus = validated_data['bus']
    pickup_date = validated_data['pickup_date']
    passenger_count = validated_data['passenger_count']
    client_amount = validated_data.get('total_amount')
    
    # Step 1: Calculate expected amount (server-side)
    expected_amount = calculate_booking_price(
        bus=bus,
        pickup_date=pickup_date,
        passenger_count=passenger_count
    )
    
    # Step 2: Verify client didn't manipulate
    if client_amount and abs(client_amount - expected_amount) > Decimal('1.00'):
        # Error Code: BOK-SERV-VAL-008
        logger.warning(
            'Price manipulation attempt',
            extra={'expected': expected_amount, 'client': client_amount}
        )
        raise ValidationError(
            f'Amount mismatch. Expected ₹{expected_amount}',
            code='BOK-SERV-VAL-008'
        )
    
    # Step 3: Use server-calculated amount
    booking = Booking.objects.create(
        total_amount=expected_amount,  # Never client_amount!
        ...
    )
```

**Rationale:** Stripe payments - client is untrusted, recalculate everything.

---

### Rule 9: Verify Webhook Signatures
```python
# ❌ NEVER - Trust webhook without signature
@api_view(['POST'])
def payment_webhook(request):
    payment_id = request.data['payment_id']
    Payment.objects.filter(id=payment_id).update(status='captured')

# ✅ ALWAYS - HMAC signature verification
import hmac
import hashlib

@api_view(['POST'])
@permission_classes([AllowAny])  # Webhook, not user
def cashfree_webhook(request):
    # Step 1: Extract signature
    timestamp = request.headers.get('x-webhook-timestamp', '')
    signature = request.headers.get('x-webhook-signature', '')
    
    # Step 2: Compute expected signature
    raw_body = request.body.decode('utf-8')
    payload = timestamp + raw_body
    expected_sig = hmac.new(
        settings.CASHFREE_SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Step 3: Constant-time comparison (prevents timing attacks)
    if not hmac.compare_digest(signature, expected_sig):
        # Error Code: PAY-VIEWS-AUTH-001
        logger.warning('Invalid webhook signature', extra={'ip': get_client_ip(request)})
        return Response({'error': 'Invalid signature'}, status=401)
    
    # Step 4: Now safe to process
    data = request.data
    # ... payment processing ...
```

**Rationale:** Stripe webhooks - unsigned webhooks = free money for attackers.

---

### Rule 10: Validate Payment Amount Matches Booking
```python
# ❌ NEVER - Confirm payment without amount check
def confirm_payment(payment_id):
    Payment.objects.filter(id=payment_id).update(status='captured')

# ✅ ALWAYS - Verify amount from gateway matches expected
@transaction.atomic
def confirm_payment(*, payment, actual_amount_from_gateway):
    # Stripe principle: Never trust that customer paid the right amount
    if actual_amount_from_gateway != payment.amount:
        # Error Code: PAY-SERV-VAL-001
        logger.error(
            'Payment amount mismatch',
            extra={
                'payment_id': payment.id,
                'expected': payment.amount,
                'actual': actual_amount_from_gateway
            }
        )
        payment.status = 'failed'
        payment.metadata = {
            'failure_reason': 'amount_mismatch',
            'expected': str(payment.amount),
            'actual': str(actual_amount_from_gateway)
        }
        payment.save()
        raise ValidationError('Amount mismatch', code='PAY-SERV-VAL-001')
    
    # Now safe to confirm
    payment.status = 'captured'
    payment.save()
```

---

### Rule 11: Use Decimal for Money (Never Float)
```python
# ❌ NEVER - Float loses precision
total = 10.10
commission = total * 0.1  # 1.0100000000000002
platform_fee = total - commission  # 9.089999999999998

# ✅ ALWAYS - Decimal with explicit rounding
from decimal import Decimal, ROUND_HALF_UP

total = Decimal('10.10')
commission = (total * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
platform_fee = total - commission  # Exact: 9.09

# ✅ Model definition
class Booking(models.Model):
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
```

**Rationale:** Banking systems - float arithmetic loses cents, Decimal doesn't.

---

## 🛡️ INPUT VALIDATION (DEFENSE IN DEPTH)

### Rule 12: Validate at Every Layer
```python
# Serializer layer (API boundary)
class BookingSerializer(serializers.ModelSerializer):
    def validate_pickup_date(self, value):
        """Validate pickup date is future."""
        if value < timezone.localdate():
            # Error Code: BOK-SERIAL-VAL-010
            raise serializers.ValidationError(
                'Pickup date must be today or later',
                code='BOK-SERIAL-VAL-010'
            )
        return value

# Service layer (business logic boundary)
@transaction.atomic
def create_booking(*, validated_data, customer):
    """Create booking with availability check."""
    pickup_date = validated_data['pickup_date']
    
    # Revalidate (serializer might be bypassed)
    if pickup_date < timezone.localdate():
        # Error Code: BOK-SERV-VAL-009
        raise ValidationError('Past date not allowed', code='BOK-SERV-VAL-009')
    
    # ... business logic ...

# Model layer (database boundary)
class Booking(models.Model):
    def clean(self):
        """Model-level validation."""
        super().clean()
        if self.pickup_date < timezone.localdate():
            # Error Code: BOK-MODELS-VAL-001
            raise ValidationError('Pickup must be future', code='BOK-MODELS-VAL-001')
    
    def save(self, *args, **kwargs):
        # Always validate before save
        self.full_clean()
        super().save(*args, **kwargs)
```

**Rationale:** Google principle - validate at every trust boundary, never assume prior validation.

---

### Rule 13: Soft Delete (Never Hard Delete Money)
```python
# ❌ NEVER - Hard delete financial records
def destroy(self, request, pk=None):
    booking = self.get_object()
    booking.delete()  # Gone forever!

# ✅ ALWAYS - Soft delete with audit trail
def destroy(self, request, pk=None):
    booking = self.get_object()
    
    # Check if deletion is allowed
    if booking.payment_status == 'fully_paid':
        # Error Code: BOK-VIEWS-PERM-004
        raise PermissionDenied('Cannot delete paid booking', code='...')
    
    # Soft delete
    booking.is_deleted = True
    booking.deleted_at = timezone.now()
    booking.deleted_by = request.user
    booking.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    # Audit log
    BookingHistory.objects.create(
        booking=booking,
        old_status=booking.status,
        new_status='deleted',
        changed_by=request.user
    )
    
    return Response(status=204)
```

**Rationale:** Sarbanes-Oxley compliance - financial records must be retained, not deleted.

---

## 🧪 ERROR HANDLING & OBSERVABILITY

### Rule 14: Structured Error Codes (MANDATORY)
```python
# ❌ NEVER - Generic errors
raise ValidationError('Something went wrong')
raise PermissionDenied('Not allowed')

# ✅ ALWAYS - Structured with error code
# Error Code: [APP]-[FILE]-[TYPE]-[NUMBER]
# Message: [User-friendly message]
# Cause: [Technical reason]
# Solution: [How to fix]

if not user.is_verified:
    # Error Code: BUS-VIEWS-PERM-003
    # Message: Operator account must be verified
    # Cause: User attempted action before verification complete
    # Solution: Complete document verification process
    raise PermissionDenied(
        'Operator account must be verified to create buses',
        code='BUS-VIEWS-PERM-003'
    )
```

**Error Code Structure:**
```
[APP]-[FILE]-[TYPE]-[NUMBER]

APP: USR, BUS, BOK, PAY, REV, DOC
FILE: MODELS, VIEWS, SERV, SERIAL
TYPE: VAL, PERM, AUTH, CONFLICT, DB, API
NUMBER: Sequential (001, 002, 003...)
```

**Rationale:** Google/Stripe - structured errors enable automated debugging and metrics.

---

### Rule 15: Log Security Events
```python
import logging

# Configure structured logging
logger = logging.getLogger(__name__)

# Log security-relevant events
if not hmac.compare_digest(signature, expected):
    logger.warning(
        'Invalid webhook signature attempt',
        extra={
            'error_code': 'PAY-VIEWS-AUTH-001',
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'payment_id': payment_id
        }
    )

# Log financial operations
logger.info(
    'Payment confirmed',
    extra={
        'payment_id': payment.id,
        'amount': str(payment.amount),
        'booking_id': booking.id,
        'customer_id': customer.id
    }
)

# NEVER log sensitive data
logger.info(f'User {user.email}')  # ❌ PII in logs
logger.info(f'User {user.id}')  # ✅ Use ID not PII
```

**Rationale:** SOC 2 compliance - audit logs required for security incidents.

---

## 🔧 PRODUCTION CONFIGURATION

### Rule 16: Secure Defaults for Production
```python
import sys

# Detect environment
IS_TESTING = config('TESTING', default=False, cast=bool) or 'test' in sys.argv
IS_PRODUCTION = config('ENV', default='development') == 'production'

# Secret key (fail fast if missing in production)
SECRET_KEY = config(
    'DJANGO_SECRET_KEY',
    default='test-secret-key' if IS_TESTING else None
)
if not SECRET_KEY and not IS_TESTING:
    raise RuntimeError('DJANGO_SECRET_KEY must be set in production')

# Debug (never true in production)
DEBUG = config('DEBUG', default=False, cast=bool)
if DEBUG and IS_PRODUCTION:
    raise RuntimeError('DEBUG must be False in production')

# Database SSL (required in production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': config(
                'DB_SSLMODE',
                default='require' if IS_PRODUCTION else 'disable'
            )
        }
    }
}

# Security headers (production only)
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

---

### Rule 17: Rate Limiting on Sensitive Endpoints
```python
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle

# Per-endpoint throttle
class OTPThrottle(AnonRateThrottle):
    rate = '5/hour'  # 5 OTP per hour per IP

class PaymentWebhookThrottle(ScopedRateThrottle):
    scope = 'webhook'  # Defined in settings

# Apply to view
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPThrottle])
def send_otp(request):
    # ... OTP logic ...
    pass

# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'webhook': '1000/day'  # Cashfree webhook limit
    }
}
```

**Rationale:** DDoS protection + cost control (SMS/API costs).

---

## 📋 CODE REVIEW CHECKLIST (Before Every Commit)
```markdown
Security:
- [ ] No hardcoded secrets or API keys
- [ ] All user input validated at serializer + service + model
- [ ] Permission checked on every endpoint (role + is_verified + is_active)
- [ ] Sensitive data encrypted at rest (bank_account, pan_number)
- [ ] Webhook signatures verified (HMAC)
- [ ] No SQL injection (using ORM only)
- [ ] CSRF tokens present

Race Conditions:
- [ ] select_for_update() used before check-then-act
- [ ] Counters incremented atomically (F() expressions)
- [ ] Aggregates recalculated under lock
- [ ] @transaction.atomic on multi-step operations

Financial:
- [ ] Money amounts recalculated server-side (never trusted from client)
- [ ] Decimal used (never float)
- [ ] Payment amounts verified against booking
- [ ] Refund logic validated
- [ ] Commission calculations audited

Data Integrity:
- [ ] full_clean() called in save()
- [ ] Soft delete for financial records
- [ ] Audit trail for all state changes
- [ ] Foreign keys have on_delete handlers

Performance:
- [ ] N+1 queries eliminated (select_related/prefetch_related)
- [ ] Pagination on large lists
- [ ] Indexes on filtered fields
- [ ] External APIs called async (Celery)

Observability:
- [ ] Error codes on all exceptions
- [ ] Security events logged
- [ ] Financial operations logged (no PII)
- [ ] Metrics for critical paths

Error Handling:
- [ ] All errors have 4-line comment (Code/Message/Cause/Solution)
- [ ] Error codes registered in ERROR_REGISTRY.md
- [ ] User-friendly error messages
- [ ] No sensitive data in errors

Production:
- [ ] Secure defaults (fail fast on missing env vars)
- [ ] Rate limiting on auth/payment endpoints
- [ ] HTTPS enforced
- [ ] Security headers configured
```

---

## 🎯 FINAL STANDARD

**Every code suggestion must pass:**

1. ✅ **Google Security Review** - No vulnerabilities
2. ✅ **Stripe Payment Audit** - Money is safe
3. ✅ **Meta Concurrency Test** - No race conditions
4. ✅ **Amazon Code Review** - Maintainable & documented
5. ✅ **SOC 2 Compliance** - Audit trail present

**If any check fails → Revise before suggesting.**

---

**END OF FAANG-LEVEL COPILOT INSTRUCTIONS**

*Version: 3.0 - Security & Race Condition Hardened*  
*Prevents: 90% of bugs found in production reviews*  
*Last Updated: 2026-02-14*