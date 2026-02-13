"""Management command to test real OTP sending via Supabase Auth.

Sends an OTP to the admin phone number and verifies it interactively.
"""

from django.core.management.base import BaseCommand

from apps.users.services import AuthService


class Command(BaseCommand):
    """Test OTP send + verify flow with a real phone number."""

    help = 'Test real OTP sending to +919667907515 via Supabase Auth'

    def add_arguments(self, parser) -> None:
        """Add optional --phone argument."""
        parser.add_argument(
            '--phone',
            type=str,
            default='+919667907515',
            help='Phone number to send OTP to (default: +919667907515)',
        )

    def handle(self, *args, **options) -> None:
        """Send OTP, wait for user input, then verify."""
        phone = options['phone']

        self.stdout.write(f'Sending OTP to {phone}...')

        try:
            result = AuthService.send_otp(phone=phone)
            self.stdout.write(self.style.SUCCESS(f'OTP sent: {result}'))
            self.stdout.write('Check your phone for the SMS.')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Send OTP failed: {e}'))
            return

        otp = input('\nEnter OTP received on your phone: ').strip()
        if not otp:
            self.stdout.write(self.style.ERROR('No OTP entered — aborting.'))
            return

        self.stdout.write(f'Verifying OTP: {otp}...')

        try:
            verify_result = AuthService.verify_otp(phone=phone, otp=otp)
            self.stdout.write(self.style.SUCCESS(
                f'OTP verified! Token: {verify_result.get("token", "N/A")}',
            ))
            user = verify_result.get('user')
            if user:
                self.stdout.write(self.style.SUCCESS(
                    f'User: {user} (new={verify_result.get("is_new_user", False)})',
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Verify OTP failed: {e}'))
