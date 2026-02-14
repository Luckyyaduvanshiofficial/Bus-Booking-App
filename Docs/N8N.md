# N8N Automation Workflows — Bus Booking Platform

**Purpose:** Complete list of N8N workflows to fully automate the Bus Booking Platform.  
**Integration Method:** Django REST API → N8N Webhooks / Scheduled Triggers  
**Last Updated:** 2025-07-13

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Authentication & Onboarding](#1-authentication--onboarding)
3. [Booking Lifecycle](#2-booking-lifecycle)
4. [Payment & Financial](#3-payment--financial)
5. [Operator Management](#4-operator-management)
6. [Document Management](#5-document-management)
7. [Review & Moderation](#6-review--moderation)
8. [Notifications Hub](#7-notifications-hub)
9. [Marketing & Engagement](#8-marketing--engagement)
10. [Admin Monitoring & Alerts](#9-admin-monitoring--alerts)
11. [Data & Reporting](#10-data--reporting)
12. [Maintenance & Cleanup](#11-maintenance--cleanup)
13. [Integration Setup Guide](#integration-setup-guide)

---

## Architecture Overview

```
┌──────────────────┐    Webhook POST     ┌──────────────┐
│  Django Backend   │ ──────────────────► │     N8N      │
│  (REST API)       │                     │  (Workflows) │
│                   │ ◄────────────────── │              │
│  signals.py /     │   API Callbacks     │  Triggers:   │
│  services.py      │                     │  - Webhook   │
│                   │                     │  - Cron      │
└──────────────────┘                     │  - Schedule  │
                                          └──────┬───────┘
                                                 │
                                    ┌────────────┼────────────┐
                                    ▼            ▼            ▼
                              ┌──────────┐ ┌──────────┐ ┌──────────┐
                              │  Email   │ │   SMS    │ │ WhatsApp │
                              │ (SMTP/   │ │ (MSG91)  │ │ (Twilio/ │
                              │ SendGrid)│ │          │ │  WABA)   │
                              └──────────┘ └──────────┘ └──────────┘
                                    │            │            │
                              ┌─────┴────────────┴────────────┴─────┐
                              │         Google Sheets / Slack /     │
                              │         Discord / Telegram          │
                              └─────────────────────────────────────┘
```

**How it works:**
1. Django fires a POST to N8N webhook URL after key events (in `services.py` or via Django signals)
2. N8N receives the webhook, runs the workflow (send email, SMS, Slack alert, etc.)
3. N8N scheduled triggers run cron-based workflows (reports, reminders, cleanup)

---

## 1. Authentication & Onboarding

### WF-AUTH-001: Welcome Email After Registration
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/user-registered` (fired after `register()` in `users/views.py`) |
| **Payload** | `{ user_id, name, phone, role, created_at }` |
| **Actions** | 1. Send welcome email (SendGrid/SMTP) with platform guide<br>2. Send welcome SMS via MSG91<br>3. If `role == operator` → send operator onboarding checklist email<br>4. Log to Google Sheet "New Users" |
| **Benefit** | First impression, reduces drop-off, guides users to complete profile |

### WF-AUTH-002: OTP Security Alert
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/otp-sent` (fired after `send_otp()`) |
| **Payload** | `{ phone, ip_address, user_agent, timestamp }` |
| **Actions** | 1. If same phone gets 3+ OTPs in 1 hour → send admin Slack alert<br>2. If IP is from unusual geo → flag as suspicious<br>3. Log all OTP attempts to Google Sheet for audit |
| **Benefit** | Detect brute-force OTP attacks, compliance audit trail |

### WF-AUTH-003: Login Notification Email
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/user-logged-in` (fired after `verify_otp()` succeeds) |
| **Payload** | `{ user_id, phone, name, ip_address, device, timestamp }` |
| **Actions** | 1. Send "New login detected" email with device/IP info<br>2. If new device/IP → send additional security warning<br>3. Log to "Login Activity" Google Sheet |
| **Benefit** | Security awareness, detect unauthorized access |

### WF-AUTH-004: Profile Completion Reminder
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 10:00 AM IST |
| **Actions** | 1. Query Django API: users with `name == '' OR city == '' OR email == ''`<br>2. Filter: registered > 24 hours ago, profile < 50% complete<br>3. Send "Complete your profile" email/SMS with deep link<br>4. If no action after 3 reminders → stop (don't spam) |
| **Benefit** | Increases profile completion rate, better search/matching |

### WF-AUTH-005: Inactive User Re-engagement
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every Monday at 9:00 AM IST |
| **Actions** | 1. Query Django API: users who haven't logged in for 14+ days<br>2. Segment: customers vs operators<br>3. Send personalized re-engagement email:<br>&nbsp;&nbsp;- Customers: "New buses available in your city"<br>&nbsp;&nbsp;- Operators: "You have X pending inquiries"<br>4. If 30+ days inactive → send "We miss you" with discount code |
| **Benefit** | Reactivation, reduce churn |

---

## 2. Booking Lifecycle

### WF-BOK-001: Booking Created — Notify Operator
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/booking-created` (fired after `BookingService.create_booking()`) |
| **Payload** | `{ booking_id, booking_number, customer_name, customer_phone, operator_id, operator_phone, bus_name, pickup_date, dropoff_date, pickup_location, dropoff_location, total_amount, trip_type, purpose }` |
| **Actions** | 1. Send SMS to operator: "New booking request #{booking_number} for {bus_name}"<br>2. Send email to operator with full booking details + accept/reject links<br>3. Send WhatsApp message to operator (if WABA configured)<br>4. Send confirmation email to customer: "Your booking request is submitted"<br>5. Start a 4-hour timer → if no response, trigger WF-BOK-002 |
| **Benefit** | Instant operator notification, reduces response time |

### WF-BOK-002: Operator Response Reminder
| Field | Value |
|-------|-------|
| **Trigger** | N8N Wait node (4 hours after WF-BOK-001) OR Cron: every 4 hours |
| **Actions** | 1. Query API: bookings with `status == PENDING` AND `created_at > 4 hours ago`<br>2. Send reminder SMS/email to operator: "Booking #{number} awaiting your response"<br>3. Send 2nd reminder at 8 hours<br>4. Send 3rd reminder at 16 hours with "Auto-cancel warning"<br>5. If 24 hours passed → booking auto-expires (handled by Celery task) |
| **Benefit** | Faster operator response, better customer experience |

### WF-BOK-003: Booking Confirmed by Operator
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/booking-confirmed` (fired after `BookingService.respond_to_booking(action='accept')`) |
| **Payload** | `{ booking_id, booking_number, customer_id, customer_phone, customer_email, bus_name, pickup_date, total_amount, payment_mode }` |
| **Actions** | 1. Send SMS to customer: "Your booking #{number} is CONFIRMED!"<br>2. Send detailed confirmation email with:<br>&nbsp;&nbsp;- Booking summary<br>&nbsp;&nbsp;- Bus details + photo<br>&nbsp;&nbsp;- Driver contact (when assigned)<br>&nbsp;&nbsp;- Payment instructions<br>&nbsp;&nbsp;- Calendar invite (.ics attachment)<br>3. Send WhatsApp confirmation to customer<br>4. If `payment_mode == online_full/online_advance` → send payment link<br>5. Create Google Calendar event for operator |
| **Benefit** | Professional confirmation, reduces customer anxiety |

### WF-BOK-004: Booking Rejected by Operator
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/booking-rejected` (fired after `BookingService.respond_to_booking(action='reject')`) |
| **Payload** | `{ booking_id, booking_number, customer_id, rejection_reason, bus_name, pickup_date, original_search_params }` |
| **Actions** | 1. Send "Booking not available" SMS/email to customer with reason<br>2. Suggest alternative buses: query API for similar routes/dates<br>3. Include link to search results for same route/date<br>4. Offer 5% discount coupon for next booking as goodwill<br>5. Log rejection reason to analytics sheet |
| **Benefit** | Retains customer with alternatives, collects rejection data |

### WF-BOK-005: Booking Cancelled — Refund Communication
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/booking-cancelled` (fired after `BookingService.cancel_booking()`) |
| **Payload** | `{ booking_id, booking_number, cancelled_by, cancellation_reason, refund_amount, refund_percentage, customer_phone, operator_phone }` |
| **Actions** | 1. Send SMS to customer: "Booking #{number} cancelled. Refund ₹{amount} initiated"<br>2. Send detailed cancellation email with refund timeline<br>3. Notify operator via SMS/email<br>4. If `cancelled_by == operator` → send apology + discount to customer<br>5. If refund_amount > 0 → trigger refund tracking workflow (WF-PAY-003)<br>6. Log cancellation to analytics sheet with reason |
| **Benefit** | Transparent communication, refund visibility |

### WF-BOK-006: Trip Reminder (Day Before)
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 6:00 PM IST |
| **Actions** | 1. Query API: confirmed bookings with `pickup_date == tomorrow`<br>2. Send customer SMS/email: "Your bus trip is tomorrow! Details..."<br>3. Include: pickup time, location, bus number, driver contact<br>4. Send operator reminder: "You have a trip tomorrow for booking #{number}"<br>5. Send WhatsApp with Google Maps link to pickup location |
| **Benefit** | Reduces no-shows, improves preparedness |

### WF-BOK-007: Trip Day Morning Reminder
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 7:00 AM IST |
| **Actions** | 1. Query API: confirmed bookings with `pickup_date == today`<br>2. Send customer SMS: "Your bus arrives today! Track live..."<br>3. Send operator SMS: "Trip day! Booking #{number} pickup at {time}"<br>4. Push notification trigger (if Firebase integrated) |
| **Benefit** | Day-of awareness, reduces missed pickups |

### WF-BOK-008: Trip Completed — Feedback Request
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/booking-completed` (fired after `BookingService.complete_booking()`) |
| **Payload** | `{ booking_id, booking_number, customer_id, customer_phone, operator_id, bus_id, bus_name }` |
| **Actions** | 1. Wait 2 hours (let customer settle)<br>2. Send "How was your trip?" email with star rating + review link<br>3. Send SMS: "Rate your {bus_name} trip → [review_link]"<br>4. If no review after 3 days → send reminder<br>5. If no review after 7 days → offer 2% discount for reviewing |
| **Benefit** | Increases review count, improves platform trust |

### WF-BOK-009: Booking Expired — Customer Notification
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/booking-expired` (fired from `expire_pending_bookings` Celery task) |
| **Payload** | `{ booking_id, booking_number, customer_phone, refund_amount, bus_name }` |
| **Actions** | 1. Send SMS: "Your booking #{number} expired. Refund ₹{amount} processed"<br>2. Send email with: expiry reason, refund details, link to rebook<br>3. Suggest similar buses for same route/date<br>4. Notify operator: "Booking expired due to no response" |
| **Benefit** | Keeps customer in loop, encourages rebooking |

---

## 3. Payment & Financial

### WF-PAY-001: Payment Successful
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/payment-success` (fired after `PaymentService.confirm_payment()`) |
| **Payload** | `{ payment_id, booking_number, amount, payment_mode, customer_phone, customer_email, cf_order_id }` |
| **Actions** | 1. Send payment receipt email (PDF attachment generated via N8N)<br>2. Send SMS: "₹{amount} received for booking #{number}"<br>3. Send WhatsApp receipt<br>4. Update Google Sheet "Revenue Tracker"<br>5. If `payment_mode == online_advance` → send "Remaining balance: ₹{x}" |
| **Benefit** | Instant payment confirmation, digital receipts |

### WF-PAY-002: Payment Failed
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/payment-failed` (from Cashfree webhook handler) |
| **Payload** | `{ payment_id, booking_number, amount, failure_reason, customer_phone }` |
| **Actions** | 1. Send SMS: "Payment of ₹{amount} failed. Try again → [link]"<br>2. Send email with retry link and alternative payment methods<br>3. If failed 3+ times → alert admin on Slack<br>4. Auto-retry reminder after 1 hour<br>5. If still failed after 4 hours → alert operator |
| **Benefit** | Recover failed payments, reduce revenue loss |

### WF-PAY-003: Refund Tracking
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/refund-initiated` (fired from `PaymentService.create_refund_record()`) |
| **Payload** | `{ refund_id, booking_number, amount, customer_phone, source_payment_id }` |
| **Actions** | 1. Send SMS: "Refund of ₹{amount} initiated. ETA: 5-7 business days"<br>2. Send email with refund tracking details<br>3. Schedule check: after 7 days, verify refund status via Cashfree API<br>4. If refund stuck → alert admin + send customer update<br>5. When refund completed → send "Refund received" confirmation |
| **Benefit** | Refund transparency, reduces support tickets |

### WF-PAY-004: Daily Revenue Report
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 11:59 PM IST |
| **Actions** | 1. Query API: all payments with `status == captured` for today<br>2. Calculate: total revenue, total refunds, net revenue, commission earned<br>3. Generate PDF report<br>4. Send to admin email<br>5. Post summary to Slack #finance channel<br>6. Append to Google Sheet "Daily Revenue" |
| **Benefit** | Financial visibility, no manual report generation |

### WF-PAY-005: Operator Payout Reminder
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every Monday at 10:00 AM IST |
| **Actions** | 1. Query API: completed bookings with `payout_status == pending`<br>2. Group by operator<br>3. Send admin email: "Pending payouts to process: {count} operators, ₹{total}"<br>4. Send operator SMS: "Your payout of ₹{amount} is being processed"<br>5. After payout marked as processed → send confirmation to operator |
| **Benefit** | Timely payouts, operator trust |

### WF-PAY-006: Commission Reconciliation
| Field | Value |
|-------|-------|
| **Trigger** | Cron: 1st of every month at 6:00 AM IST |
| **Actions** | 1. Query all completed bookings for previous month<br>2. Calculate commission earned per operator (based on `commission_rate`)<br>3. Cross-verify with Cashfree settlement data<br>4. Flag discrepancies > ₹100<br>5. Generate monthly reconciliation report<br>6. Send to admin email + Google Sheet |
| **Benefit** | Financial accuracy, catch discrepancies early |

---

## 4. Operator Management

### WF-OPR-001: New Operator Registration
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/operator-registered` (fired after `OperatorViewSet.register_as_operator()`) |
| **Payload** | `{ user_id, name, phone, business_name, business_type, city, state }` |
| **Actions** | 1. Send operator welcome email with onboarding checklist:<br>&nbsp;&nbsp;- Upload documents (RC, Insurance, Permit)<br>&nbsp;&nbsp;- Complete KYC (PAN, Bank Account)<br>&nbsp;&nbsp;- Add first bus listing<br>2. Send SMS: "Welcome aboard! Complete your setup → [link]"<br>3. Alert admin: "New operator registered: {business_name}"<br>4. Add to "Operators" Google Sheet<br>5. Start onboarding drip campaign (WF-OPR-002) |
| **Benefit** | Guided onboarding, faster time-to-first-booking |

### WF-OPR-002: Operator Onboarding Drip Campaign
| Field | Value |
|-------|-------|
| **Trigger** | N8N Wait nodes (chained from WF-OPR-001) |
| **Actions** | **Day 1:** "Upload your documents to get verified" email<br>**Day 3:** "Add your first bus listing" email + tutorial video link<br>**Day 5:** "Set competitive pricing — here's what others charge" email<br>**Day 7:** "Need help? Call our support" SMS<br>**Day 14:** If no bus listed → personal call alert to sales team<br>**Day 30:** If still inactive → flag account for review |
| **Benefit** | Systematic onboarding, reduces operator drop-off |

### WF-OPR-003: Operator Verified / Rejected
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/operator-verification-update` (fired after admin `verify_user()` action) |
| **Payload** | `{ user_id, name, phone, verification_status, rejection_reason }` |
| **Actions** | **If verified:**<br>1. Send congratulations email + "Add your first bus" CTA<br>2. Send SMS: "You're verified! Start listing buses"<br>3. Unlock operator dashboard access<br><br>**If rejected:**<br>1. Send email with specific rejection reason + how to fix<br>2. Send SMS: "Verification needs attention → [link]"<br>3. Allow resubmission after 24 hours |
| **Benefit** | Clear communication, faster re-verification |

### WF-OPR-004: Operator Performance Weekly Report
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every Monday at 8:00 AM IST |
| **Actions** | 1. Query operator dashboard data per operator<br>2. Generate performance summary:<br>&nbsp;&nbsp;- Total bookings this week<br>&nbsp;&nbsp;- Revenue earned<br>&nbsp;&nbsp;- Average rating<br>&nbsp;&nbsp;- Response time (avg)<br>&nbsp;&nbsp;- Cancellation rate<br>3. Send personalized email to each active operator<br>4. If rating dropped below 3.5 → include improvement tips<br>5. If cancellation rate > 20% → send warning |
| **Benefit** | Performance visibility, self-service improvement |

### WF-OPR-005: Operator Subscription Expiry Warning
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 9:00 AM IST |
| **Actions** | 1. Query: operators where `subscription_expires_at` is within 7 days<br>2. Send renewal reminder email: "Your {tier} plan expires on {date}"<br>3. At 3 days: urgent SMS reminder<br>4. At 1 day: final warning email with upgrade/renew link<br>5. On expiry day: downgrade to FREE tier + send notification |
| **Benefit** | Subscription retention, revenue protection |

### WF-OPR-006: Operator Milestone Celebrations
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/operator-milestone` (fired when total_bookings hits milestone) |
| **Payload** | `{ operator_id, name, milestone_type, value }` |
| **Actions** | Milestones: 10th booking, 50th booking, 100th booking, ₹1L revenue, ₹5L revenue<br>1. Send celebration email with badge graphic<br>2. Send SMS: "Congratulations! You've completed {X} bookings!"<br>3. For 100+ bookings → offer PRO subscription discount<br>4. Post to operator leaderboard |
| **Benefit** | Operator motivation, loyalty |

---

## 5. Document Management

### WF-DOC-001: Document Uploaded — Admin Alert
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/document-uploaded` (fired after `DocumentViewSet.create()`) |
| **Payload** | `{ document_id, user_id, operator_name, document_type, document_url }` |
| **Actions** | 1. Alert admin via Slack: "New document pending: {type} from {operator}"<br>2. Send admin email with document preview link<br>3. If queue has 10+ pending docs → escalate to senior admin<br>4. Track in "Document Queue" Google Sheet |
| **Benefit** | Fast document processing, no pending docs forgotten |

### WF-DOC-002: Document Verified / Rejected
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/document-verified` (fired after `DocumentViewSet.verify()`) |
| **Payload** | `{ document_id, user_id, phone, document_type, verification_status, rejection_reason }` |
| **Actions** | **If verified:**<br>1. Send SMS: "Your {doc_type} has been verified ✓"<br>2. Send email confirmation<br>3. Check if ALL operator docs are now verified → trigger WF-OPR-003 (auto-verify operator)<br><br>**If rejected:**<br>1. Send SMS: "Your {doc_type} was rejected. Reason: {reason}"<br>2. Send email with specific instructions for resubmission<br>3. Include re-upload link |
| **Benefit** | Instant feedback, faster operator activation |

### WF-DOC-003: Document Expiry Warning
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 8:00 AM IST |
| **Actions** | 1. Query: documents with `expiry_date` within 30 days<br>2. At 30 days: send email reminder "Your {doc_type} expires on {date}"<br>3. At 15 days: send SMS reminder<br>4. At 7 days: send urgent email + SMS + admin alert<br>5. On expiry: deactivate operator's buses + send notification<br>6. Alert admin: "Operator {name} has expired documents" |
| **Benefit** | Compliance, prevent operating with expired permits/insurance |

---

## 6. Review & Moderation

### WF-REV-001: New Review Submitted
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/review-submitted` (fired after review creation) |
| **Payload** | `{ review_id, review_type (bus/operator), reviewer_name, rating, comment, bus_name, operator_id }` |
| **Actions** | 1. Alert admin via Slack: "New review pending: {rating}★ for {bus_name}"<br>2. If `rating <= 2` → escalate as URGENT to admin<br>3. Run basic content moderation (check for profanity via API)<br>4. If clean → auto-approve (optional, based on rating threshold)<br>5. Notify operator: "You have a new {rating}★ review" |
| **Benefit** | Fast moderation, flag negative reviews early |

### WF-REV-002: Review Approved — Notify Parties
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/review-approved` (fired after `BusReviewViewSet.approve()`) |
| **Payload** | `{ review_id, bus_name, operator_id, rating, reviewer_name }` |
| **Actions** | 1. Send operator email: "New {rating}★ review on {bus_name}"<br>2. If 5★ → send congratulations + share on social prompt<br>3. If 1-2★ → send "improvement tips" email to operator<br>4. Send reviewer thank-you email<br>5. Update operator's rating stats in CRM sheet |
| **Benefit** | Feedback loop, operator improvement |

### WF-REV-003: Low Rating Alert
| Field | Value |
|-------|-------|
| **Trigger** | Webhook (from WF-REV-001 if rating <= 2) |
| **Actions** | 1. Send admin urgent Slack alert<br>2. Send operator email: "Action needed: low rating received"<br>3. If operator's `rating_avg` drops below 3.0 → trigger review of account<br>4. If 3+ low ratings in a week → temporarily reduce bus visibility<br>5. Assign customer success team follow-up |
| **Benefit** | Quality control, customer protection |

---

## 7. Notifications Hub

### WF-NOT-001: Multi-Channel Notification Dispatcher
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/send-notification` (central dispatcher for all notification types) |
| **Payload** | `{ user_id, phone, email, notification_type, title, message, metadata, channels: ['sms', 'email', 'whatsapp', 'push'] }` |
| **Actions** | Based on `channels` array:<br>1. **SMS** → MSG91 API (use template based on `notification_type`)<br>2. **Email** → SendGrid/SMTP with HTML template<br>3. **WhatsApp** → Twilio WABA or WhatsApp Business API<br>4. **Push** → Firebase Cloud Messaging<br>5. Log delivery status to Google Sheet<br>6. If delivery fails → retry once after 5 minutes |
| **Benefit** | Centralized, no duplicate notification logic across workflows |

### WF-NOT-002: Notification Preference Respector
| Field | Value |
|-------|-------|
| **Trigger** | Called by WF-NOT-001 before sending |
| **Actions** | 1. Query user's notification preferences (preferred_language, channels)<br>2. Translate message if `preferred_language == 'hi'` (Hindi)<br>3. Skip channels user has opted out of<br>4. Respect quiet hours (10 PM - 7 AM IST for non-urgent)<br>5. Rate limit: max 5 notifications per hour per user |
| **Benefit** | User respect, compliance with DND regulations |

---

## 8. Marketing & Engagement

### WF-MKT-001: Daily Promotional Emails
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 10:00 AM IST |
| **Actions** | 1. Query: featured/top-rated buses with available dates<br>2. Segment users by city<br>3. Send city-specific promotional email:<br>&nbsp;&nbsp;- "Top 5 buses available in {city} this weekend"<br>&nbsp;&nbsp;- Include ratings, prices, photos<br>4. Include seasonal offers (wedding season, festivals)<br>5. Track open/click rates |
| **Benefit** | Drive bookings, keep platform top-of-mind |

### WF-MKT-002: Festive / Seasonal Campaigns
| Field | Value |
|-------|-------|
| **Trigger** | Scheduled: specific dates (Diwali, Holi, Navratri, Christmas, Summer break etc.) |
| **Actions** | 1. 15 days before festival → send "Book early for {festival}" email<br>2. 7 days before → send SMS with discount code<br>3. Create auto-expiring coupon in Django (via API)<br>4. Send personalized emails based on past booking purposes:<br>&nbsp;&nbsp;- Wedding season → target past wedding bookers<br>&nbsp;&nbsp;- Religious → target past religious trip bookers<br>5. Post-festival: "Thank you" email with photo sharing prompt |
| **Benefit** | Seasonal revenue boost, targeted marketing |

### WF-MKT-003: Abandoned Search Follow-up
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/search-performed` (fired from `BusViewSet.search()`) + no booking in 2 hours |
| **Payload** | `{ user_id, source_city, destination_city, date, passenger_count }` |
| **Actions** | 1. Wait 2 hours<br>2. Check if user created a booking → if yes, stop<br>3. If no booking → send email: "Still looking for {route}? Here are the best options"<br>4. Include top 3 buses with prices<br>5. Offer 3% first-booking discount |
| **Benefit** | Convert search intent to bookings |

### WF-MKT-004: Repeat Booking Incentive
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/booking-completed` (same trigger as WF-BOK-008) |
| **Actions** | 1. Check customer's total completed bookings<br>2. If 2nd booking → send "Loyal customer" email + 5% discount for next<br>3. If 5th booking → send "VIP" badge email + 10% discount<br>4. If 10th booking → send exclusive offer + priority support<br>5. Generate and store coupon via Django API |
| **Benefit** | Customer retention, increase LTV |

### WF-MKT-005: Referral Program Automation
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/booking-completed` (first booking by referred user) |
| **Actions** | 1. Check if customer was referred (referral_code in metadata)<br>2. Credit referrer with ₹200 coupon via API<br>3. Credit new user with ₹100 coupon<br>4. Send "You earned ₹200!" email to referrer<br>5. Send "Your friend joined!" push notification to referrer |
| **Benefit** | Organic growth, viral acquisition |

### WF-MKT-006: Weekly Newsletter
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every Thursday at 11:00 AM IST |
| **Actions** | 1. Aggregate week's data: new buses added, top routes, featured operators<br>2. Generate HTML newsletter<br>3. Segment: send different content to customers vs operators<br>4. Customer newsletter: deals, new routes, tips<br>5. Operator newsletter: platform updates, best practices, earnings tips |
| **Benefit** | Regular engagement, brand recall |

---

## 9. Admin Monitoring & Alerts

### WF-ADM-001: Real-Time Error Alert
| Field | Value |
|-------|-------|
| **Trigger** | Webhook: `POST /n8n/error-occurred` (fired from Django error handler / middleware) |
| **Payload** | `{ error_code, error_message, endpoint, user_id, stack_trace, severity }` |
| **Actions** | 1. If `severity == critical` → immediate Slack alert + SMS to on-call<br>2. If `severity == high` → Slack alert<br>3. If `severity == medium` → log to "Errors" Google Sheet<br>4. If same error occurs 5+ times in 1 hour → escalate to critical<br>5. Create Jira/Linear ticket for recurring errors |
| **Benefit** | Instant incident awareness, faster resolution |

### WF-ADM-002: Daily Admin Dashboard Email
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 8:00 AM IST |
| **Actions** | 1. Query API aggregates:<br>&nbsp;&nbsp;- New registrations (customers + operators)<br>&nbsp;&nbsp;- Total bookings today / this week<br>&nbsp;&nbsp;- Revenue today / this week<br>&nbsp;&nbsp;- Pending operator verifications<br>&nbsp;&nbsp;- Pending document verifications<br>&nbsp;&nbsp;- Pending reviews to moderate<br>&nbsp;&nbsp;- Active coupons<br>2. Generate HTML dashboard email<br>3. Send to all admin users<br>4. Post summary to Slack #admin channel |
| **Benefit** | Admin productivity, no need to check dashboard manually |

### WF-ADM-003: Suspicious Activity Detection
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every 30 minutes |
| **Actions** | 1. Check for anomalies:<br>&nbsp;&nbsp;- User with 10+ OTP requests in 1 hour<br>&nbsp;&nbsp;- Same IP creating multiple accounts<br>&nbsp;&nbsp;- Unusual booking patterns (same customer, many cancellations)<br>&nbsp;&nbsp;- Payment amount manipulation attempts (from error logs)<br>2. Score risk level<br>3. If high risk → block account + alert admin on Slack<br>4. If medium risk → flag for manual review<br>5. Log all suspicious activities to security sheet |
| **Benefit** | Fraud prevention, platform security |

### WF-ADM-004: Pending Queue Escalation
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every 2 hours |
| **Actions** | 1. Count pending items:<br>&nbsp;&nbsp;- Operator verifications pending > 48 hours<br>&nbsp;&nbsp;- Document verifications pending > 24 hours<br>&nbsp;&nbsp;- Review moderations pending > 12 hours<br>2. If any queue exceeds threshold → Slack alert to admin<br>3. If exceeds 2x threshold → email to super admin<br>4. Generate "Pending Items" summary |
| **Benefit** | SLA enforcement, nothing falls through cracks |

### WF-ADM-005: Platform Health Check
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every 5 minutes |
| **Actions** | 1. Ping Django health endpoint<br>2. Check Celery worker status (via Flower or direct Redis check)<br>3. Check Cashfree API connectivity<br>4. Check Supabase connectivity<br>5. Check Cloudinary connectivity<br>6. If any service down → immediate Slack + SMS to on-call<br>7. Log uptime to monitoring sheet |
| **Benefit** | Instant downtime detection, proactive resolution |

### WF-ADM-006: Coupon Usage Monitoring
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 11:00 PM IST |
| **Actions** | 1. Query: all active coupons with usage stats<br>2. Flag coupons that are 80%+ exhausted<br>3. Flag expired but still active coupons (shouldn't happen, but check)<br>4. Send admin email: "Coupon status report"<br>5. If any coupon used by same user multiple times → fraud alert |
| **Benefit** | Coupon abuse prevention, budget tracking |

---

## 10. Data & Reporting

### WF-RPT-001: Weekly Business Report
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every Sunday at 8:00 PM IST |
| **Actions** | 1. Aggregate weekly metrics:<br>&nbsp;&nbsp;- Total bookings (new, confirmed, completed, cancelled)<br>&nbsp;&nbsp;- Revenue (gross, net, refunds)<br>&nbsp;&nbsp;- New users (customers + operators)<br>&nbsp;&nbsp;- Top routes, top buses, top operators<br>&nbsp;&nbsp;- Average rating trend<br>&nbsp;&nbsp;- Cancellation rate<br>2. Generate PDF report with charts (via QuickChart.io)<br>3. Send to admin + stakeholders email<br>4. Post to Slack #reports<br>5. Append to Google Sheet "Weekly Metrics" |
| **Benefit** | Data-driven decisions, investor-ready metrics |

### WF-RPT-002: Monthly Operator Statement
| Field | Value |
|-------|-------|
| **Trigger** | Cron: 1st of every month at 9:00 AM IST |
| **Actions** | 1. For each active operator:<br>&nbsp;&nbsp;- Total bookings, completed, cancelled<br>&nbsp;&nbsp;- Revenue earned, commission deducted, net payout<br>&nbsp;&nbsp;- Average rating, total reviews<br>&nbsp;&nbsp;- Bus utilization rate<br>2. Generate PDF statement per operator<br>3. Send email: "Your {month} statement is ready"<br>4. Store statement URL in operator record |
| **Benefit** | Professional statements, operator trust, tax compliance |

### WF-RPT-003: Customer Booking History Digest
| Field | Value |
|-------|-------|
| **Trigger** | Cron: 1st of every month at 10:00 AM IST |
| **Actions** | 1. For each active customer with bookings:<br>&nbsp;&nbsp;- List of trips this month<br>&nbsp;&nbsp;- Total spent<br>&nbsp;&nbsp;- Loyalty points / discount earned<br>2. Send personalized email: "Your {month} travel summary"<br>3. Include: "Book your next trip" CTA with trending routes |
| **Benefit** | Engagement, personalized experience |

### WF-RPT-004: Google Sheets Sync (Live Dashboard)
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every 6 hours |
| **Actions** | 1. Sync to Google Sheets:<br>&nbsp;&nbsp;- **Sheet 1: Users** — id, name, role, city, created_at, total_bookings<br>&nbsp;&nbsp;- **Sheet 2: Bookings** — number, status, amount, dates, customer, operator<br>&nbsp;&nbsp;- **Sheet 3: Revenue** — daily/weekly/monthly revenue<br>&nbsp;&nbsp;- **Sheet 4: Operators** — name, rating, total_buses, verification_status<br>&nbsp;&nbsp;- **Sheet 5: Reviews** — recent reviews with ratings<br>2. Auto-update linked charts in Google Data Studio |
| **Benefit** | Live business dashboard without building custom analytics |

---

## 11. Maintenance & Cleanup

### WF-MNT-001: Database Cleanup
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every Sunday at 3:00 AM IST |
| **Actions** | 1. Clean up expired tokens older than 30 days<br>2. Archive bookings older than 1 year to cold storage<br>3. Delete read notifications older than 90 days<br>4. Clean up orphaned availability blocks<br>5. Vacuum-analyze PostgreSQL tables (via management command)<br>6. Send admin report: "Cleanup completed: {items} cleaned" |
| **Benefit** | Database performance, storage cost control |

### WF-MNT-002: SSL/Domain Certificate Monitoring
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 6:00 AM IST |
| **Actions** | 1. Check SSL certificate expiry for API domain<br>2. Check SSL for frontend domain<br>3. If expiry within 30 days → alert admin email<br>4. If expiry within 7 days → urgent Slack + SMS |
| **Benefit** | Prevent SSL expiry downtime |

### WF-MNT-003: Backup Verification
| Field | Value |
|-------|-------|
| **Trigger** | Cron: Every day at 4:00 AM IST |
| **Actions** | 1. Verify latest database backup exists (Supabase/Railway backup)<br>2. Check backup size is within expected range<br>3. If no backup found → critical alert<br>4. Weekly: test restore to staging environment<br>5. Log backup status to monitoring sheet |
| **Benefit** | Data safety, disaster recovery confidence |

---

## Integration Setup Guide

### Step 1: Django Webhook Helper

Add a utility function to fire N8N webhooks from Django:

```python
# apps/common/n8n.py

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

N8N_BASE_URL = settings.N8N_WEBHOOK_URL  # e.g., "https://your-n8n.app.n8n.cloud/webhook"


def fire_n8n_webhook(event: str, payload: dict) -> None:
    """Fire an N8N webhook asynchronously (best-effort).
    
    Args:
        event: Event name (e.g., 'booking-created', 'payment-success')
        payload: Dict of event data to send
    """
    url = f"{N8N_BASE_URL}/{event}"
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=5,
            headers={'X-Webhook-Secret': settings.N8N_WEBHOOK_SECRET}
        )
        if response.status_code != 200:
            logger.warning(
                'N8N webhook failed',
                extra={'event': event, 'status': response.status_code}
            )
    except requests.RequestException as e:
        # Best-effort: don't crash app if N8N is down
        logger.error(
            'N8N webhook error',
            extra={'event': event, 'error': str(e)}
        )
```

### Step 2: Add to settings.py

```python
# N8N Configuration
N8N_WEBHOOK_URL = config('N8N_WEBHOOK_URL', default='')
N8N_WEBHOOK_SECRET = config('N8N_WEBHOOK_SECRET', default='')
```

### Step 3: Fire Webhooks from Services

```python
# Example: apps/bookings/services.py

from apps.common.n8n import fire_n8n_webhook

class BookingService:
    @staticmethod
    @transaction.atomic
    def create_booking(*, validated_data, customer):
        # ... existing logic ...
        booking = Booking.objects.create(...)
        
        # Fire N8N webhook (non-blocking, best-effort)
        fire_n8n_webhook('booking-created', {
            'booking_id': str(booking.id),
            'booking_number': booking.booking_number,
            'customer_name': customer.name,
            'customer_phone': customer.phone,
            'operator_id': str(booking.operator.id),
            'operator_phone': booking.operator.phone,
            'bus_name': booking.bus.name,
            'pickup_date': str(booking.pickup_date),
            'total_amount': str(booking.total_amount),
        })
        
        return booking
```

### Step 4: N8N Workflow Template

In N8N, create a workflow:
1. **Trigger Node:** Webhook → POST → `/booking-created`
2. **IF Node:** Check `X-Webhook-Secret` header matches
3. **SendGrid Node:** Send confirmation email
4. **MSG91 Node:** Send SMS
5. **Google Sheets Node:** Log event

### Step 5: Environment Variables

```env
# .env
N8N_WEBHOOK_URL=https://your-instance.app.n8n.cloud/webhook
N8N_WEBHOOK_SECRET=your-secure-webhook-secret-here
```

---

## Workflow Priority Matrix

| Priority | Workflow IDs | Impact | Effort |
|----------|-------------|--------|--------|
| **P0 — Launch Day** | WF-AUTH-001, WF-BOK-001, WF-BOK-003, WF-BOK-005, WF-PAY-001, WF-PAY-002 | High | Low |
| **P1 — Week 1** | WF-BOK-006, WF-BOK-008, WF-AUTH-003, WF-OPR-001, WF-DOC-002, WF-ADM-002 | High | Medium |
| **P2 — Week 2** | WF-BOK-002, WF-BOK-004, WF-BOK-009, WF-PAY-003, WF-OPR-003, WF-REV-001, WF-ADM-005 | Medium | Medium |
| **P3 — Month 1** | WF-MKT-001, WF-MKT-002, WF-AUTH-004, WF-OPR-002, WF-DOC-003, WF-RPT-001, WF-ADM-003 | Medium | High |
| **P4 — Month 2+** | WF-MKT-003, WF-MKT-004, WF-MKT-005, WF-MKT-006, WF-RPT-002, WF-RPT-003, WF-RPT-004, WF-OPR-004, WF-OPR-005, WF-OPR-006 | Lower | High |
| **P5 — Ongoing** | WF-MNT-001, WF-MNT-002, WF-MNT-003, WF-ADM-004, WF-ADM-006, WF-PAY-004, WF-PAY-005, WF-PAY-006 | Operational | Low |

---

## Total Workflow Count: 45

| Category | Count |
|----------|-------|
| Authentication & Onboarding | 5 |
| Booking Lifecycle | 9 |
| Payment & Financial | 6 |
| Operator Management | 6 |
| Document Management | 3 |
| Review & Moderation | 3 |
| Notifications Hub | 2 |
| Marketing & Engagement | 6 |
| Admin Monitoring & Alerts | 6 |
| Data & Reporting | 4 |
| Maintenance & Cleanup | 3 |
| **TOTAL** | **45** |

---

*This document covers every automation opportunity identified in the Bus Booking Platform codebase. Implement workflows in priority order (P0 → P5) for maximum impact with minimum effort.*
