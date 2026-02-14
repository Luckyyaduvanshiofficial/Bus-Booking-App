# Notification System - Brevo Integration Guide

## Overview

The notification system uses **Brevo** (formerly Sendinblue) for:
- ✅ **WhatsApp Marketing** - Trip reminders, booking updates
- ✅ **Transactional Emails** - Booking confirmations, payment receipts

**Architecture**: Django → n8n → Brevo → Customer

---

## 🚀 Quick Start

### 1. Get Brevo API Key
1. Sign up at [Brevo.com](https://www.brevo.com/)
2. Go to **Settings → API Keys**
3. Create new API key with permissions:
   - `Email campaigns` (Send transactional emails)
   - `WhatsApp campaigns` (Send WhatsApp messages)

### 2. Configure WhatsApp Sender
1. In Brevo dashboard: **Conversations → WhatsApp**
2. Connect your WhatsApp Business Account
3. Copy your WhatsApp sender number (e.g., `+919876543210`)

### 3. Add to .env
```bash
BREVO_API_KEY=xkeysib-abc123...
BREVO_WHATSAPP_SENDER=+919876543210
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/notifications
```

---

## 🔧 n8n Workflow Setup

### Workflow Structure
```
HTTP Webhook (POST)
    ↓
Switch (by event type)
    ├─ booking_created → WhatsApp + Email
    ├─ booking_confirmed → WhatsApp + Email
    ├─ booking_rejected → WhatsApp + Email
    ├─ trip_reminder → WhatsApp only
    └─ payment_received → Email only
```

---

### Node 1: HTTP Webhook
```json
{
  "method": "POST",
  "path": "notifications",
  "responseMode": "responseNode",
  "options": {}
}
```

**Payload Structure**:
```json
{
  "event": "booking_confirmed",
  "notification_id": "uuid",
  "channels": {
    "whatsapp": true,
    "email": true
  },
  "recipients": {
    "phone": "+919876543210",
    "email": "customer@example.com",
    "name": "Customer Name"
  },
  "title": "Booking Confirmed - BK-123",
  "message": "Your booking has been confirmed...",
  "metadata": {
    "booking_id": "uuid",
    "booking_number": "BK-123"
  }
}
```

---

### Node 2: Switch by Event Type
```
Switch on: {{$json.event}}

Outputs:
1. booking_created
2. booking_confirmed
3. booking_rejected
4. trip_reminder
5. payment_received
```

---

### Node 3a: Send WhatsApp (Brevo Conversations API)

**HTTP Request Node**:
```json
{
  "method": "POST",
  "url": "https://api.brevo.com/v3/conversations/messages",
  "authentication": "headerAuth",
  "headerParameters": {
    "api-key": "={{$env.BREVO_API_KEY}}",
    "content-type": "application/json"
  },
  "bodyParameters": {
    "receiverType": "whatsapp",
    "senderNumber": "={{$env.BREVO_WHATSAPP_SENDER}}",
    "receiverNumber": "={{$json.recipients.phone}}",
    "text": "={{$json.message}}"
  }
}
```

**Brevo WhatsApp API Docs**: [https://developers.brevo.com/docs/whatsapp-api](https://developers.brevo.com/docs/whatsapp-api)

**Supported Features**:
- ✅ Text messages
- ✅ Emojis
- ✅ Links
- ✅ Template messages (pre-approved by WhatsApp)

**Rate Limits**:
- Free Plan: 100 WhatsApp messages/month
- Starter Plan: 1,000 WhatsApp messages/month
- Business Plan: 10,000 WhatsApp messages/month

---

### Node 3b: Send Email (Brevo SMTP API)

**HTTP Request Node**:
```json
{
  "method": "POST",
  "url": "https://api.brevo.com/v3/smtp/email",
  "authentication": "headerAuth",
  "headerParameters": {
    "api-key": "={{$env.BREVO_API_KEY}}",
    "content-type": "application/json"
  },
  "bodyParameters": {
    "sender": {
      "name": "Bus Booking Platform",
      "email": "noreply@busbooking.com"
    },
    "to": [{
      "email": "={{$json.recipients.email}}",
      "name": "={{$json.recipients.name}}"
    }],
    "subject": "={{$json.title}}",
    "htmlContent": "<html><body><h1>={{$json.title}}</h1><p style=\"white-space:pre-wrap\">={{$json.message}}</p></body></html>"
  }
}
```

**Brevo Email API Docs**: [https://developers.brevo.com/docs/send-a-transactional-email](https://developers.brevo.com/docs/send-a-transactional-email)

**Supported Features**:
- ✅ HTML emails
- ✅ Attachments (PDFs for booking confirmations)
- ✅ Templates
- ✅ Dynamic content
- ✅ Tracking (opens, clicks)

**Rate Limits**:
- Free Plan: 300 emails/day
- Starter Plan: 10,000 emails/month
- Business Plan: 20,000 emails/month

---

### Node 4: Respond to Webhook
```json
{
  "statusCode": 200,
  "body": {
    "status": "success",
    "notification_id": "={{$json.notification_id}}"
  }
}
```

---

## 📱 WhatsApp Template Messages

For **WhatsApp Business**, pre-approved templates are required for marketing messages.

### Create Template in Brevo

1. Go to **Conversations → Templates**
2. Click **Create Template**
3. Add template (must be approved by WhatsApp):

**Template Name**: `booking_confirmed`
```
Hi {{1}},

✅ Your booking {{2}} has been confirmed!

🚍 Bus: {{3}}
📅 Date: {{4}}
🕒 Time: {{5}}
📍 Pickup: {{6}}

Have a safe journey!

- Bus Booking Team
```

4. Submit for WhatsApp approval (takes 1-2 days)
5. Once approved, use in n8n:

```json
{
  "method": "POST",
  "url": "https://api.brevo.com/v3/conversations/messages",
  "bodyParameters": {
    "receiverType": "whatsapp",
    "senderNumber": "={{$env.BREVO_WHATSAPP_SENDER}}",
    "receiverNumber": "={{$json.recipients.phone}}",
    "template": {
      "name": "booking_confirmed",
      "language": "en",
      "bodyParameters": [
        "={{$json.recipients.name}}",
        "={{$json.metadata.booking_number}}",
        "={{$json.metadata.bus_name}}",
        "={{$json.metadata.pickup_date}}",
        "={{$json.metadata.pickup_time}}",
        "={{$json.metadata.pickup_location}}"
      ]
    }
  }
}
```

---

## 🧪 Testing

### Test WhatsApp Message
```bash
curl -X POST https://api.brevo.com/v3/conversations/messages \
  -H "api-key: YOUR_BREVO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "receiverType": "whatsapp",
    "senderNumber": "+919876543210",
    "receiverNumber": "+919876543211",
    "text": "🚌 Test notification from Bus Booking Platform"
  }'
```

### Test Email
```bash
curl -X POST https://api.brevo.com/v3/smtp/email \
  -H "api-key: YOUR_BREVO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": {
      "name": "Bus Booking",
      "email": "noreply@busbooking.com"
    },
    "to": [{
      "email": "test@example.com",
      "name": "Test User"
    }],
    "subject": "Test Email",
    "htmlContent": "<h1>Test</h1><p>This is a test email</p>"
  }'
```

### Test via Django Shell
```python
from apps.common.notification_service import NotificationService
from apps.users.models import CustomUser

user = CustomUser.objects.get(phone='+919876543210')

NotificationService.create_notification(
    user=user,
    notification_type='booking_confirmed',
    title='Test Notification',
    message='This is a test WhatsApp message',
    send_whatsapp=True,
    send_email=True
)
```

---

## 💰 Brevo Pricing

### Free Plan (Good for Development)
- 300 emails/day
- 100 WhatsApp messages/month
- All API features

### Starter Plan ($25/month)
- 10,000 emails/month
- 1,000 WhatsApp messages/month
- Email templates
- WhatsApp templates

### Business Plan ($65/month)
- 20,000 emails/month
- 10,000 WhatsApp messages/month
- Marketing automation
- A/B testing
- Advanced analytics

**Recommendation**: Start with **Free Plan** for development, then upgrade to **Starter** for production.

---

## 🔍 Monitoring

### Brevo Dashboard
- **Email Stats**: Go to **Statistics → Email**
  - Sent, delivered, opened, clicked
  - Bounces, spam reports
  
- **WhatsApp Stats**: Go to **Conversations → Statistics**
  - Messages sent, delivered, read
  - Response rate

### Django Logs
```bash
# Filter notification logs
tail -f logs/django.log | grep "Notification"

# Failed Brevo webhooks
tail -f logs/django.log | grep "NOT-SERV-API"
```

### n8n Execution History
- Go to n8n dashboard
- Click **Executions** tab
- Check success/failure rate
- View error logs for failed executions

---

## 🚨 Troubleshooting

### WhatsApp Not Sending

**Issue**: `401 Unauthorized`
- ✅ Check `BREVO_API_KEY` is correct
- ✅ API key has `WhatsApp campaigns` permission

**Issue**: `403 Forbidden - Sender not verified`
- ✅ WhatsApp Business Account connected in Brevo
- ✅ `BREVO_WHATSAPP_SENDER` matches verified number

**Issue**: `400 Bad Request - Template not approved`
- ✅ Template submitted for WhatsApp approval
- ✅ Use plain text for non-template messages

### Email Not Sending

**Issue**: `401 Unauthorized`
- ✅ Check `BREVO_API_KEY` is correct

**Issue**: `400 Bad Request - Invalid sender email`
- ✅ Sender email verified in Brevo
- ✅ Go to **Senders → Add a sender** to verify

**Issue**: Emails in spam
- ✅ Set up SPF/DKIM records (Brevo provides them)
- ✅ Use verified sender domain

---

## 📊 Best Practices

### 1. Rate Limiting
```python
# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'whatsapp': '10/minute',  # Don't spam WhatsApp
        'email': '50/minute',
    }
}
```

### 2. Message Formatting
```python
# ✅ GOOD - Clear, actionable
message = (
    f"✅ Booking Confirmed - {booking_number}\n\n"
    f"Bus: {bus_name}\n"
    f"Date: {pickup_date}\n"
    f"Time: {pickup_time}\n"
    f"Pickup: {pickup_location}\n\n"
    f"See you soon!"
)

# ❌ BAD - Vague, no context
message = "Your booking is confirmed"
```

### 3. Opt-out Management
- Add "Reply STOP to unsubscribe" to WhatsApp messages
- Store `user.whatsapp_opt_out = True` in database
- Check before sending:
  ```python
  if user.whatsapp_opt_out:
      send_whatsapp = False
  ```

---

## 🔄 Migration from MSG91

If migrating from MSG91 SMS to Brevo WhatsApp:

1. **Update user phone numbers**:
   - Ensure format: `+91XXXXXXXXXX` (E.164 format)
   - Update database: `UPDATE users SET phone = '+91' || phone WHERE phone NOT LIKE '+%'`

2. **Update message templates**:
   - WhatsApp supports emojis ✅
   - WhatsApp supports links
   - Keep messages under 1024 characters

3. **Update notification types**:
   - Keep all existing notification types
   - Just change delivery method from SMS → WhatsApp

4. **Run migration**:
   ```bash
   python manage.py makemigrations users
   python manage.py migrate
   ```

---

## 📝 Summary

✅ **WhatsApp**: Brevo Conversations API → Marketing messages, trip reminders  
✅ **Email**: Brevo SMTP API → Booking confirmations, payment receipts  
✅ **n8n**: Routes notifications from Django to Brevo  
✅ **Free Plan**: 300 emails/day + 100 WhatsApp/month (good for development)  
✅ **Paid Plan**: $25/month for 10K emails + 1K WhatsApp (production)

**Next Steps**:
1. Create Brevo account
2. Get API key
3. Connect WhatsApp Business
4. Configure n8n workflow
5. Test end-to-end flow

---

**Last Updated**: 2026-02-14  
**Brevo Docs**: https://developers.brevo.com/  
**Support**: https://help.brevo.com/
