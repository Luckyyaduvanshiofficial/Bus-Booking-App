"""
Management command to reconcile pending payments with Cashfree gateway.

Usage:
    python manage.py reconcile_payments
    python manage.py reconcile_payments --older-than-hours 24
    python manage.py reconcile_payments --dry-run

Error Codes:
    PAY-MGMT-API-001: Cashfree API call failed
    PAY-MGMT-CONFIG-001: Cashfree credentials missing
"""
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Payment, Booking

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reconcile pending payments with Cashfree payment gateway"

    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than-hours',
            type=int,
            default=1,
            help='Only reconcile payments older than N hours (default: 1)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of payments to reconcile (default: 100)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview reconciliation without making changes',
        )

    def handle(self, *args, **options):
        older_than_hours = options['older_than_hours']
        limit = options['limit']
        dry_run = options['dry_run']

        cutoff_time = timezone.now() - timedelta(hours=older_than_hours)

        # Find stale pending payments
        stale_payments = Payment.objects.filter(
            status__in=[
                Payment.CfStatus.CREATED,
                Payment.CfStatus.ACTIVE,
            ],
            created_at__lt=cutoff_time,
        ).select_related('booking', 'booking__customer')[:limit]

        total_count = stale_payments.count()
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ No stale payments found older than {older_than_hours}h'
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f'🔍 Found {total_count} stale payments to reconcile'
            )
        )

        reconciled = 0
        updated = 0
        failed = 0

        for payment in stale_payments:
            try:
                result = self._reconcile_payment(payment, dry_run)
                reconciled += 1

                if result['updated']:
                    updated += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ {payment.id}: {result["old_status"]} → {result["new_status"]}'
                        )
                    )
                else:
                    self.stdout.write(
                        f'⏸️  {payment.id}: {result["status"]} (no change)'
                    )

            except Exception as e:
                failed += 1
                logger.exception(
                    'reconciliation_failed',
                    extra={
                        'payment_id': str(payment.id),
                        'booking_id': str(payment.booking_id),
                    },
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ {payment.id}: {e}'
                    )
                )

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Reconciled: {reconciled}/{total_count} | '
                f'Updated: {updated} | Failed: {failed}'
            )
        )
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  DRY RUN - No changes made'))

    def _reconcile_payment(
        self,
        payment: Payment,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Fetch payment status from Cashfree and update if needed."""
        from django.conf import settings

        app_id = getattr(settings, 'CASHFREE_APP_ID', None)
        secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', None)

        if not app_id or not secret_key:
            logger.warning(
                'cashfree_credentials_missing',
                extra={'error_code': 'PAY-MGMT-CONFIG-001'},
            )
            raise ValueError('Cashfree credentials not configured')

        # Fetch order from Cashfree
        order_id = payment.cf_order_id or str(payment.id)
        gateway_status = self._fetch_cashfree_order_status(
            order_id=order_id,
            app_id=app_id,
            secret_key=secret_key,
        )

        if not gateway_status.get('success'):
            raise Exception(
                f"Gateway API failed: {gateway_status.get('reason')}"
            )

        cf_order_status = gateway_status['response'].get('order_status', '').upper()
        old_status = payment.status

        # Map Cashfree status to our status
        new_status = self._map_cashfree_status(cf_order_status)

        if new_status and new_status != old_status:
            if not dry_run:
                with transaction.atomic():
                    payment.status = new_status
                    payment.metadata = {
                        **(payment.metadata or {}),
                        'reconciled_at': timezone.now().isoformat(),
                        'gateway_status': cf_order_status,
                    }
                    payment.save(update_fields=['status', 'metadata'])

                    # Update booking if payment captured
                    if new_status == Payment.CfStatus.CAPTURED:
                        self._update_booking_on_capture(payment)

                logger.info(
                    'payment_reconciled',
                    extra={
                        'payment_id': str(payment.id),
                        'old_status': old_status,
                        'new_status': new_status,
                        'cf_status': cf_order_status,
                    },
                )

            return {
                'updated': True,
                'old_status': old_status,
                'new_status': new_status,
            }

        return {
            'updated': False,
            'status': old_status,
        }

    def _fetch_cashfree_order_status(
        self,
        order_id: str,
        app_id: str,
        secret_key: str,
    ) -> Dict[str, Any]:
        """Fetch order status from Cashfree API."""
        from django.conf import settings
        import requests
        from requests import RequestException

        is_test = app_id.startswith('TEST')
        base_url = (
            'https://sandbox.cashfree.com/pg'
            if is_test
            else 'https://api.cashfree.com/pg'
        )

        headers = {
            'x-client-id': app_id,
            'x-client-secret': secret_key,
            'x-api-version': settings.CASHFREE_API_VERSION,
        }

        try:
            response = requests.get(
                f'{base_url}/orders/{order_id}',
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'response': response.json(),
                }
            else:
                logger.error(
                    'cashfree_api_failed',
                    extra={
                        'error_code': 'PAY-MGMT-API-001',
                        'status_code': response.status_code,
                        'response': response.text[:500],
                    },
                )
                return {
                    'success': False,
                    'reason': 'gateway_error',
                    'status_code': response.status_code,
                }

        except RequestException as exc:
            logger.error(
                'cashfree_request_failed',
                extra={
                    'error_code': 'PAY-MGMT-API-001',
                    'error': str(exc),
                },
            )
            return {
                'success': False,
                'reason': 'request_failed',
                'error': str(exc),
            }

    def _map_cashfree_status(self, cf_status: str) -> Optional[str]:
        """Map Cashfree order status to our Payment.CfStatus."""
        mapping = {
            'ACTIVE': Payment.CfStatus.ACTIVE,
            'PAID': Payment.CfStatus.CAPTURED,
            'EXPIRED': Payment.CfStatus.FAILED,
            'CANCELLED': Payment.CfStatus.FAILED,
            'TERMINATED': Payment.CfStatus.FAILED,
        }
        return mapping.get(cf_status)

    def _update_booking_on_capture(self, payment: Payment) -> None:
        """Update booking status when payment is captured."""
        booking = Booking.objects.select_for_update().get(pk=payment.booking_id)

        # Update payment status
        if payment.payment_type == 'advance':
            if booking.payment_status != Booking.PaymentStatus.PARTIALLY_PAID:
                booking.payment_status = Booking.PaymentStatus.PARTIALLY_PAID
                booking.save(update_fields=['payment_status'])
        else:
            if booking.payment_status != Booking.PaymentStatus.FULLY_PAID:
                booking.payment_status = Booking.PaymentStatus.FULLY_PAID
                booking.save(update_fields=['payment_status'])

        # Auto-confirm if pending
        if booking.status == Booking.Status.PENDING:
            booking.transition_to(Booking.Status.CONFIRMED)
            booking.save(update_fields=['status'])
