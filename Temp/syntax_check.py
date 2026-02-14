import py_compile
import sys

files = [
    'backend/apps/bookings/services.py',
    'backend/apps/bookings/views.py',
    'backend/apps/bookings/urls.py',
    'backend/apps/bookings/serializers.py',
    'backend/apps/bookings/models.py',
    'backend/apps/users/services.py',
    'backend/apps/users/views.py',
    'backend/apps/users/serializers.py',
    'backend/apps/buses/serializers.py',
    'backend/apps/reviews/models.py',
    'backend/apps/reviews/views.py',
    'backend/apps/common/authentication.py',
    'backend/bus_booking/settings.py',
]

errors = []
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"[OK] {f}")
    except py_compile.PyCompileError as e:
        errors.append((f, str(e)))
        print(f"[ERR] {f}: {e}")

if errors:
    print(f"\n{len(errors)} file(s) with syntax errors:")
    for f, e in errors:
        print(f"  - {f}")
    sys.exit(1)
else:
    print(f"\nAll {len(files)} files passed syntax check!")
    sys.exit(0)
