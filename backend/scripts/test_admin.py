#!/usr/bin/env python
"""
Admin Panel Smoke-Test Script.

Verifies that every registered ModelAdmin page loads without errors.
Run: python scripts/test_admin.py

Requires:
  - DJANGO_SETTINGS_MODULE set or defaulted to bus_booking.settings
  - An active superuser in the database
  - Server NOT required (uses Django test client)

Exit Codes:
  0: All admin pages load successfully
  1: One or more pages failed
"""
import os
import sys
import django

# ---------------------------------------------------------------------------
# Bootstrap Django
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bus_booking.settings')
django.setup()

from django.contrib.admin.sites import site as admin_site  # noqa: E402
from django.test import RequestFactory  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()

# ---------------------------------------------------------------------------
# Colour helpers (Windows-safe fallback)
# ---------------------------------------------------------------------------

def _green(text: str) -> str:
    return f"\033[92m{text}\033[0m"

def _red(text: str) -> str:
    return f"\033[91m{text}\033[0m"

def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Test every registered ModelAdmin changelist URL.

    Returns:
        int: 0 if all pass, 1 if any fail.
    """
    print(_bold("\n=== Admin Panel Smoke Test ===\n"))

    # Step 1: Get or create a superuser for the test client
    superuser = User.objects.filter(is_superuser=True).first()
    if superuser is None:
        print(_red("ERROR: No superuser found. Create one first:"))
        print("  python manage.py createsuperuser")
        return 1

    print(f"Using superuser: {superuser.phone} (ID: {superuser.pk})\n")

    # Step 2: Build a fake request as superuser
    factory = RequestFactory()

    # Step 3: Iterate over every registered model
    models_registered = list(admin_site._registry.items())
    print(f"Found {len(models_registered)} registered admin models.\n")

    passed = 0
    failed = 0
    errors: list[str] = []

    for model, model_admin in models_registered:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        url = f"/admin/{app_label}/{model_name}/"

        try:
            # Create GET request and attach superuser
            request = factory.get(url)
            request.user = superuser

            # Call changelist_view (this exercises list_display, list_filter, etc.)
            response = model_admin.changelist_view(request)

            if response.status_code == 200:
                print(f"  {_green('PASS')}  {app_label}.{model_name} → {url}")
                passed += 1
            else:
                msg = f"  {_red('FAIL')}  {app_label}.{model_name} → HTTP {response.status_code}"
                print(msg)
                errors.append(msg)
                failed += 1
        except Exception as exc:
            msg = f"  {_red('FAIL')}  {app_label}.{model_name} → {type(exc).__name__}: {exc}"
            print(msg)
            errors.append(msg)
            failed += 1

    # Step 4: Summary
    print(f"\n{'='*50}")
    print(f"Total: {passed + failed}  |  {_green(f'Pass: {passed}')}  |  {_red(f'Fail: {failed}')}")

    if errors:
        print(f"\n{_red('Failed pages:')}")
        for e in errors:
            print(f"  {e}")

    print()
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
