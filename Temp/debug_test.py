"""Diagnostic script to debug refund test failures."""
import os, sys, logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bus_booking.settings')

import django
django.setup()

# Patch _refund_after_commit to capture exceptions
import apps.bookings.services as svc
_original_schedule = svc.PaymentService.schedule_booking_refund_post_commit

def debug_schedule(*, booking_id, amount, reason=''):
    """Wrapper that logs exceptions from the on_commit callback."""
    from decimal import Decimal
    from django.db import transaction
    from apps.bookings.models import Booking
    
    normalized_amount = amount.quantize(Decimal('0.01'))
    if normalized_amount <= Decimal('0.00'):
        return

    def _debug_refund_after_commit():
        print(f"[DEBUG] _refund_after_commit CALLED for booking {booking_id}, amount={normalized_amount}", flush=True)
        try:
            booking = Booking.objects.get(pk=booking_id)
            print(f"[DEBUG] Got booking: {booking.id}, payment_status={booking.payment_status}", flush=True)
            refunded_total = svc.PaymentService.process_booking_refund(
                booking=booking,
                amount=normalized_amount,
                reason=reason,
            )
            print(f"[DEBUG] refunded_total={refunded_total}, normalized_amount={normalized_amount}", flush=True)
            if (
                refunded_total >= normalized_amount
                and booking.payment_status != Booking.PaymentStatus.REFUNDED
            ):
                booking.payment_status = Booking.PaymentStatus.REFUNDED
                booking.save(update_fields=['payment_status'])
                print(f"[DEBUG] Set payment_status to REFUNDED", flush=True)
            else:
                print(f"[DEBUG] NOT updating payment_status: refunded_total >= normalized_amount = {refunded_total >= normalized_amount}", flush=True)
        except Booking.DoesNotExist:
            print(f"[DEBUG] Booking {booking_id} does not exist!", flush=True)
        except Exception as e:
            print(f"[DEBUG] EXCEPTION in _refund_after_commit: {type(e).__name__}: {e}", flush=True)
            import traceback
            traceback.print_exc()

    transaction.on_commit(_debug_refund_after_commit)

svc.PaymentService.schedule_booking_refund_post_commit = staticmethod(debug_schedule)

# Now run the test
import unittest
from apps.bookings.tests import BookingServiceTest

suite = unittest.TestSuite()
suite.addTest(BookingServiceTest('test_cancel_booking_sets_refund_for_captured_payment'))
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
