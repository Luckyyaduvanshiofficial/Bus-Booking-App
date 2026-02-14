# ✅ Task 5: Notification System - UPDATED (Brevo Integration)

## 🔄 Changes Made

Updated notification system to use **Brevo** (formerly Sendinblue) instead of MSG91/SendGrid:
- ✅ **WhatsApp Marketing** via Brevo Conversations API (replaces SMS)
- ✅ **Transactional Emails** via Brevo SMTP API (replaces SendGrid)
- ✅ Single platform for both channels
- ✅ Cost-effective ($25/month for 10K emails + 1K WhatsApp)

---

## 📝 Files Changed

### 1. Model Changes
**File**: `apps/users/models.py`
- ✅ Changed `sms_sent` → `whatsapp_sent`
- ✅ Changed `sms_sent_at` → `whatsapp_sent_at`
- ✅ Updated model comments to reflect Brevo

### 2. Serializer Updates
**File**: `apps/users/serializers.py`
- ✅ Updated `NotificationSerializer` fields
- ✅ Changed `sms_sent` → `whatsapp_sent`

### 3. Service Layer
**File**: `apps/common/notification_service.py`
- ✅ Changed `send_sms` parameter → `send_whatsapp`
- ✅ Updated docstrings to reference Brevo
- ✅ Updated webhook payload with `channels.whatsapp`
- ✅ Updated delivery tracking fields

### 4. Celery Tasks
**File**: `apps/common/tasks.py`
- ✅ Updated `send_notification_via_n8n` to use `send_whatsapp`
- ✅ Updated `send_trip_reminders` to send WhatsApp (not SMS)
- ✅ Updated docstrings

### 5. Booking Service Integration
**File**: `apps/bookings/services.py`
- ✅ All notifications now use `send_whatsapp=True` instead of `send_sms=True`
- ✅ Updated comments

### 6. Configuration
**File**: `bus_booking/settings.py`
- ✅ Added `BREVO_API_KEY` config
- ✅ Added `BREVO_WHATSAPP_SENDER` config
- ✅ Marked MSG91 as legacy

**File**: `.env.example`
- ✅ Added Brevo configuration
- ✅ Added example WhatsApp sender number

### 7. Documentation
**File**: `BREVO_INTEGRATION_GUIDE.md` (NEW)
- ✅ Complete Brevo setup guide
- ✅ WhatsApp template creation guide
- ✅ n8n workflow configuration
- ✅ API testing examples
- ✅ Pricing comparison
- ✅ Troubleshooting guide

---

## 🎯 Notification Flow (Updated)

```
Customer creates booking
    ↓
BookingService.create_notification(send_whatsapp=True, send_email=True)
    ↓
Create DB record + Trigger Celery task
    ↓
send_notification_via_n8n.delay()
    ↓
Celery Worker → n8n webhook
    ↓
n8n routes by event type
    ├─ WhatsApp via Brevo Conversations API
    └─ Email via Brevo SMTP API
```

---

## 📋 Updated Requirements

### Environment Variables
```bash
# Brevo Configuration
BREVO_API_KEY=xkeysib-abc123...
BREVO_WHATSAPP_SENDER=+919876543210

# n8n Webhook
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/notifications
```

### Brevo Account Setup
1. ✅ Sign up at [Brevo.com](https://www.brevo.com/)
2. ✅ Get API key with permissions:
   - Email campaigns
   - WhatsApp campaigns
3. ✅ Connect WhatsApp Business Account
4. ✅ Verify sender email domain

---

## 🔧 n8n Workflow Updates

### WhatsApp Node (Brevo Conversations API)
```json
{
  "method": "POST",
  "url": "https://api.brevo.com/v3/conversations/messages",
  "headers": {
    "api-key": "={{$env.BREVO_API_KEY}}"
  },
  "body": {
    "receiverType": "whatsapp",
    "senderNumber": "={{$env.BREVO_WHATSAPP_SENDER}}",
    "receiverNumber": "={{$json.recipients.phone}}",
    "text": "={{$json.message}}"
  }
}
```

### Email Node (Brevo SMTP API)
```json
{
  "method": "POST",
  "url": "https://api.brevo.com/v3/smtp/email",
  "headers": {
    "api-key": "={{$env.BREVO_API_KEY}}"
  },
  "body": {
    "sender": {
      "name": "Bus Booking",
      "email": "noreply@busbooking.com"
    },
    "to": [{
      "email": "={{$json.recipients.email}}",
      "name": "={{$json.recipients.name}}"
    }],
    "subject": "={{$json.title}}",
    "htmlContent": "<h1>={{$json.title}}</h1><p style=\"white-space:pre-wrap\">={{$json.message}}</p>"
  }
}
```

---

## 💰 Cost Comparison

### Old Stack (MSG91 + SendGrid)
- MSG91 SMS: ₹0.25/SMS × 1000 = ₹250/month
- SendGrid: $15/month (10K emails)
- **Total**: ~₹1,500/month

### New Stack (Brevo)
- Brevo Starter: $25/month
  - 10,000 emails
  - 1,000 WhatsApp messages
- **Total**: ₹2,100/month (~$25)

**Savings**: None, but unified platform + WhatsApp marketing capability

---

## ✅ What Changed from SMS to WhatsApp

| Feature | Old (SMS) | New (WhatsApp) |
|---------|-----------|----------------|
| Delivery | MSG91 SMS | Brevo WhatsApp Marketing |
| Cost | ₹0.25/message | Included in plan |
| Rich Media | ❌ Plain text only | ✅ Emojis, links, images |
| Templates | ❌ No templates | ✅ Pre-approved templates |
| Character Limit | 160 chars | 1024 chars |
| Delivery Confirmation | ✅ Yes | ✅ Read receipts |
| Two-way Communication | ❌ No | ✅ Yes |
| Marketing | ❌ No | ✅ Yes (campaigns) |

---

## 📱 WhatsApp Template Requirements

For marketing messages, WhatsApp requires pre-approved templates:

### Example Template: `booking_confirmed`
```
Hi {{1}},

✅ Your booking {{2}} has been confirmed!

🚍 Bus: {{3}}
📅 Date: {{4}}
🕒 Time: {{5}}
📍 Pickup: {{6}}

Have a safe journey!
```

**Approval Time**: 1-2 business days

**Usage in n8n**:
```json
{
  "template": {
    "name": "booking_confirmed",
    "language": "en",
    "bodyParameters": [
      "Customer Name",
      "BK-123",
      "Luxury Coach",
      "15 Feb 2026",
      "08:00 AM",
      "Jaipur Railway Station"
    ]
  }
}
```

---

## 🧪 Testing

### Test WhatsApp Delivery
```bash
curl -X POST https://api.brevo.com/v3/conversations/messages \
  -H "api-key: YOUR_BREVO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "receiverType": "whatsapp",
    "senderNumber": "+919876543210",
    "receiverNumber": "+919876543211",
    "text": "🚌 Test: Your booking has been confirmed!"
  }'
```

### Test Email Delivery
```bash
curl -X POST https://api.brevo.com/v3/smtp/email \
  -H "api-key: YOUR_BREVO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": {"email": "noreply@busbooking.com"},
    "to": [{"email": "test@example.com"}],
    "subject": "Test Email",
    "htmlContent": "<h1>Test</h1>"
  }'
```

---

## 📊 Migration Steps

### 1. Database Migration
```bash
# Create migration for field rename
python manage.py makemigrations users

# Expected migration:
# - Rename field: sms_sent → whatsapp_sent
# - Rename field: sms_sent_at → whatsapp_sent_at

python manage.py migrate
```

### 2. Brevo Setup
1. Create Brevo account
2. Get API key
3. Connect WhatsApp Business Account
4. Verify sender email
5. Add to `.env`:
   ```bash
   BREVO_API_KEY=xkeysib-...
   BREVO_WHATSAPP_SENDER=+919876543210
   ```

### 3. n8n Workflow Update
1. Replace MSG91 node with Brevo WhatsApp node
2. Replace SendGrid node with Brevo Email node
3. Test webhook endpoint
4. Deploy workflow

### 4. Testing
```bash
# Run notification tests
python manage.py test apps.common.tests_notifications -v 2

# Manual test
python manage.py shell
>>> from apps.common.notification_service import NotificationService
>>> from apps.users.models import CustomUser
>>> user = CustomUser.objects.first()
>>> NotificationService.create_notification(
...     user=user,
...     notification_type='booking_confirmed',
...     title='Test',
...     message='Test WhatsApp message',
...     send_whatsapp=True,
...     send_email=True
... )
```

---

## 🎉 Benefits of Brevo

### Unified Platform
- ✅ WhatsApp + Email in one dashboard
- ✅ Single API key
- ✅ Unified analytics
- ✅ Easier to manage

### Cost-Effective
- ✅ Free Plan: 300 emails/day + 100 WhatsApp/month
- ✅ Starter Plan: $25/month for 10K emails + 1K WhatsApp
- ✅ No per-message charges

### Marketing Features
- ✅ WhatsApp campaigns
- ✅ Email campaigns
- ✅ Marketing automation
- ✅ A/B testing
- ✅ Segmentation

### Better Deliverability
- ✅ Dedicated IPs available
- ✅ SPF/DKIM/DMARC setup
- ✅ WhatsApp Business verified
- ✅ Better inbox placement

---

## 🚨 Important Notes

### WhatsApp Template Approval
- **Required**: For marketing messages
- **Approval Time**: 1-2 business days
- **Alternative**: Use plain text for transactional messages (no template needed)

### Phone Number Format
- **Required**: E.164 format (`+919876543210`)
- **Update Database**: 
  ```sql
  UPDATE users 
  SET phone = CONCAT('+91', phone) 
  WHERE phone NOT LIKE '+%';
  ```

### Rate Limits
- **WhatsApp**: 1,000 messages/month (Starter Plan)
- **Email**: 10,000 emails/month (Starter Plan)
- **Upgrade**: Business Plan for higher limits

---

## 📚 Resources

- **Brevo Docs**: https://developers.brevo.com/
- **WhatsApp API**: https://developers.brevo.com/docs/whatsapp-api
- **Email API**: https://developers.brevo.com/docs/send-a-transactional-email
- **Templates**: https://help.brevo.com/hc/en-us/articles/360001004660
- **Pricing**: https://www.brevo.com/pricing/

---

## ✅ Checklist

- [x] Updated models (whatsapp_sent fields)
- [x] Updated serializers
- [x] Updated notification service
- [x] Updated Celery tasks
- [x] Updated booking service integration
- [x] Updated configuration files
- [x] Created Brevo integration guide
- [ ] Run database migration
- [ ] Create Brevo account
- [ ] Get Brevo API key
- [ ] Connect WhatsApp Business
- [ ] Update n8n workflow
- [ ] Test WhatsApp delivery
- [ ] Test email delivery
- [ ] Deploy to production

---

**Implementation Date**: 2026-02-14  
**Platform**: Brevo (WhatsApp + Email)  
**Status**: ✅ Code Updated, Ready for Migration  

**Next Step**: Run `python manage.py makemigrations users` to create migration for field rename.
