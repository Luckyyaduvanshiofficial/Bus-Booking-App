---
trigger: always_on
description: backend-api-integration
---

Name: backend-api-integration

Content:

1. Backend runs at http://localhost:8000/api/v1/
2. All requests need Authorization header: Token <token>
3. Django returns Decimals as strings - always parse with parseFloat()
4. Django returns dates in ISO format - parse with new Date()
5. Backend error format: { error: string, code: string }
6. Map error codes to user messages using ERROR_MESSAGES constant
7. Example error codes:
   - BOK-SERV-CONFLICT-001: "Bus not available on selected date"
   - PAY-SERV-VAL-001: "Payment verification failed"
   - USR-SERV-AUTH-003: "Invalid credentials"
