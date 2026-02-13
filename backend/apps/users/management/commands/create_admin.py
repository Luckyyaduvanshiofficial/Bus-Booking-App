"""Management command to create the platform admin superuser.

Creates Lucky Yaduvanshi as the superuser with phone-based auth.
"""

from django.core.management.base import BaseCommand

from apps.users.models import CustomUser


class Command(BaseCommand):
    """Create the initial admin superuser for the Bus Booking Platform."""

    help = 'Create superuser for Lucky Yaduvanshi (+919667907515)'

    def handle(self, *args, **options) -> None:
        """Create the superuser if not already present.

        Uses phone as USERNAME_FIELD. Sets role=admin, is_verified=True.
        Skips validation to avoid password-related full_clean issues.
        """
        phone = '+919667907515'

        if CustomUser.objects.filter(phone=phone).exists():
            self.stdout.write(self.style.WARNING(
                f'User {phone} already exists — skipping creation.',
            ))
            return

        user = CustomUser(
            phone=phone,
            username=phone,
            name='Lucky Yaduvanshi',
            role=CustomUser.Role.ADMIN,
            is_verified=True,
            verification_status=CustomUser.VerificationStatus.VERIFIED,
            is_staff=True,
            is_superuser=True,
        )
        user.set_password('Busbook@2026')
        user.save(skip_validation=True)

        self.stdout.write(self.style.SUCCESS(
            f'Superuser created: {phone} (Lucky Yaduvanshi)',
        ))
