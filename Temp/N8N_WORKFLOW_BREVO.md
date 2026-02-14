# n8n Workflow - Brevo Integration (Quick Setup)

## 🚀 Complete n8n Workflow JSON

Copy and paste this into n8n to create the complete workflow:

```json
{
  "name": "Bus Booking Notifications (Brevo)",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "notifications",
        "responseMode": "responseNode",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "webhookId": "your-webhook-id"
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.event}}",
              "operation": "equals",
              "value2": "booking_created"
            }
          ]
        }
      },
      "name": "If Booking Created",
      "type": "n8n-nodes-base.if",
      "position": [450, 200]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.event}}",
              "operation": "equals",
              "value2": "booking_confirmed"
            }
          ]
        }
      },
      "name": "If Booking Confirmed",
      "type": "n8n-nodes-base.if",
      "position": [450, 350]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.event}}",
              "operation": "equals",
              "value2": "trip_reminder"
            }
          ]
        }
      },
      "name": "If Trip Reminder",
      "type": "n8n-nodes-base.if",
      "position": [450, 500]
    },
    {
      "parameters": {
        "url": "https://api.brevo.com/v3/conversations/messages",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "brevoApi",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "api-key",
              "value": "={{$credentials.apiKey}}"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "receiverType",
              "value": "whatsapp"
            },
            {
              "name": "senderNumber",
              "value": "={{$env.BREVO_WHATSAPP_SENDER}}"
            },
            {
              "name": "receiverNumber",
              "value": "={{$json.recipients.phone}}"
            },
            {
              "name": "text",
              "value": "={{$json.message}}"
            }
          ]
        },
        "options": {}
      },
      "name": "Send WhatsApp (Brevo)",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300]
    },
    {
      "parameters": {
        "url": "https://api.brevo.com/v3/smtp/email",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "brevoApi",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "api-key",
              "value": "={{$credentials.apiKey}}"
            }
          ]
        },
        "sendBody": true,
        "jsonParameters": true,
        "bodyParametersJson": "={\n  \"sender\": {\n    \"name\": \"Bus Booking Platform\",\n    \"email\": \"noreply@busbooking.com\"\n  },\n  \"to\": [{\n    \"email\": \"{{$json.recipients.email}}\",\n    \"name\": \"{{$json.recipients.name}}\"\n  }],\n  \"subject\": \"{{$json.title}}\",\n  \"htmlContent\": \"<html><body><h1>{{$json.title}}</h1><p style='white-space:pre-wrap'>{{$json.message}}</p></body></html>\"\n}",
        "options": {}
      },
      "name": "Send Email (Brevo)",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 450]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={\"status\": \"success\", \"notification_id\": \"{{$json.notification_id}}\"}",
        "options": {}
      },
      "name": "Respond to Webhook",
      "type": "n8n-nodes-base.respondToWebhook",
      "position": [850, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "If Booking Created",
            "type": "main",
            "index": 0
          },
          {
            "node": "If Booking Confirmed",
            "type": "main",
            "index": 0
          },
          {
            "node": "If Trip Reminder",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "If Booking Created": {
      "main": [
        [
          {
            "node": "Send WhatsApp (Brevo)",
            "type": "main",
            "index": 0
          },
          {
            "node": "Send Email (Brevo)",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "If Booking Confirmed": {
      "main": [
        [
          {
            "node": "Send WhatsApp (Brevo)",
            "type": "main",
            "index": 0
          },
          {
            "node": "Send Email (Brevo)",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "If Trip Reminder": {
      "main": [
        [
          {
            "node": "Send WhatsApp (Brevo)",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send WhatsApp (Brevo)": {
      "main": [
        [
          {
            "node": "Respond to Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send Email (Brevo)": {
      "main": [
        [
          {
            "node": "Respond to Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

---

## 📝 Setup Steps

### 1. Create Brevo Credentials in n8n
1. Click **Credentials** → **New**
2. Search for "Brevo"
3. Add credentials:
   - **API Key**: Your Brevo API key (`xkeysib-...`)
4. Save as "Brevo API"

### 2. Add Environment Variable
1. Go to n8n **Settings** → **Environment Variables**
2. Add variable:
   - **Key**: `BREVO_WHATSAPP_SENDER`
   - **Value**: `+919876543210` (your WhatsApp sender)

### 3. Import Workflow
1. Click **Workflows** → **Import from File**
2. Paste the JSON above
3. Or manually create nodes as shown below

### 4. Activate Workflow
1. Click **Active** toggle to enable
2. Copy webhook URL
3. Add to Django `.env`:
   ```bash
   N8N_WEBHOOK_URL=https://your-n8n.com/webhook-test/notifications
   ```

---

## 🧩 Node Configuration Details

### Node 1: Webhook Trigger
```
Type: Webhook
Method: POST
Path: notifications
Response Mode: Using Respond to Webhook Node
```

### Node 2-4: If Conditions (Switch)
```
Type: IF
Condition 1: {{$json.event}} equals "booking_created"
Condition 2: {{$json.event}} equals "booking_confirmed"
Condition 3: {{$json.event}} equals "trip_reminder"
```

### Node 5: Send WhatsApp (Brevo)
```
Type: HTTP Request
Method: POST
URL: https://api.brevo.com/v3/conversations/messages

Headers:
  api-key: {{$credentials.apiKey}}

Body (JSON):
{
  "receiverType": "whatsapp",
  "senderNumber": "{{$env.BREVO_WHATSAPP_SENDER}}",
  "receiverNumber": "{{$json.recipients.phone}}",
  "text": "{{$json.message}}"
}
```

### Node 6: Send Email (Brevo)
```
Type: HTTP Request
Method: POST
URL: https://api.brevo.com/v3/smtp/email

Headers:
  api-key: {{$credentials.apiKey}}

Body (JSON):
{
  "sender": {
    "name": "Bus Booking Platform",
    "email": "noreply@busbooking.com"
  },
  "to": [{
    "email": "{{$json.recipients.email}}",
    "name": "{{$json.recipients.name}}"
  }],
  "subject": "{{$json.title}}",
  "htmlContent": "<html><body><h1>{{$json.title}}</h1><p style='white-space:pre-wrap'>{{$json.message}}</p></body></html>"
}
```

### Node 7: Respond to Webhook
```
Type: Respond to Webhook
Response Code: 200
Response Body:
{
  "status": "success",
  "notification_id": "{{$json.notification_id}}"
}
```

---

## 🧪 Test Workflow

### Test Payload
```bash
curl -X POST https://your-n8n.com/webhook-test/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "event": "booking_confirmed",
    "notification_id": "test-123",
    "channels": {
      "whatsapp": true,
      "email": true
    },
    "recipients": {
      "phone": "+919876543210",
      "email": "test@example.com",
      "name": "Test Customer"
    },
    "title": "Booking Confirmed - BK-123",
    "message": "Your booking has been confirmed!\n\nBooking: BK-123\nBus: Luxury Coach\nDate: 15 Feb 2026",
    "metadata": {
      "booking_id": "uuid-here"
    }
  }'
```

### Expected Result
- ✅ WhatsApp message sent to `+919876543210`
- ✅ Email sent to `test@example.com`
- ✅ n8n returns 200 OK with `{"status": "success"}`

---

## 🐛 Troubleshooting

### Error: "Invalid API key"
- ✅ Check Brevo credentials in n8n
- ✅ Regenerate API key in Brevo dashboard

### Error: "Sender number not verified"
- ✅ Check `BREVO_WHATSAPP_SENDER` matches verified number
- ✅ Connect WhatsApp Business in Brevo dashboard

### Error: "Webhook not responding"
- ✅ Check workflow is **Active**
- ✅ Click **Test Workflow** to see execution logs
- ✅ Check n8n **Executions** tab for errors

### WhatsApp Not Sending
- ✅ Check phone number format: `+919876543210` (E.164)
- ✅ Check message length (< 1024 chars)
- ✅ Check Brevo WhatsApp quota (100/month on free plan)

### Email Not Sending
- ✅ Check sender email verified in Brevo
- ✅ Check recipient email valid
- ✅ Check Brevo email quota (300/day on free plan)

---

## 📊 Monitoring

### n8n Execution History
- Go to **Executions** tab
- Filter by **Error** to see failures
- Click execution to see detailed logs

### Brevo Dashboard
- **WhatsApp**: Conversations → Statistics
- **Email**: Statistics → Email
- Check delivery rate, open rate, click rate

---

## 🎯 Production Checklist

- [ ] Brevo credentials added in n8n
- [ ] `BREVO_WHATSAPP_SENDER` environment variable set
- [ ] Workflow tested with test payload
- [ ] WhatsApp delivery confirmed
- [ ] Email delivery confirmed
- [ ] Webhook URL added to Django `.env`
- [ ] Workflow activated (toggle on)
- [ ] Monitoring dashboard bookmarked

---

**Quick Help**:
- Brevo API Docs: https://developers.brevo.com/
- n8n Docs: https://docs.n8n.io/
- Support: Check Brevo/n8n community forums
