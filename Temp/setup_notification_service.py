"""Temporary script to create notification service files."""
import os

# Create services directory
os.makedirs('apps/common/services', exist_ok=True)

# Create __init__.py
with open('apps/common/services/__init__.py', 'w') as f:
    f.write('"""Common services package."""\n')

print("Created apps/common/services directory")
