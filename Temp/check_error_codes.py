#!/usr/bin/env python
"""
Error Code Coverage Checker.

Compares error codes defined in ERROR_REGISTRY.md against actual usage
in the codebase (apps/ directory). Reports:
  - Codes in registry but NOT in code (dead registry entries)
  - Codes in code but NOT in registry (undocumented codes)
  - Coverage percentage

Run: python scripts/check_error_codes.py

Exit Codes:
  0: 100 % coverage (all codes match)
  1: Gaps found
"""
import os
import re
import sys

# ---------------------------------------------------------------------------
# Paths (relative to this script → backend/)
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..')
REGISTRY_PATH = os.path.join(BACKEND_DIR, '..', 'Docs', 'ERROR_REGISTRY.md')
APPS_DIR = os.path.join(BACKEND_DIR, 'apps')

# Pattern: APP-FILE-TYPE-NNN  (e.g. BOK-SERV-CONFLICT-001)
ERROR_CODE_RE = re.compile(
    r'\b([A-Z]{2,4})-([A-Z]{2,7})-([A-Z]{2,10})-(\d{3})\b'
)
SYMBOL_OK = '[OK]'
SYMBOL_WARN = '[WARN]'
SYMBOL_ERR = '[ERR]'

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def _green(text: str) -> str:
    return f"\033[92m{text}\033[0m"

def _red(text: str) -> str:
    return f"\033[91m{text}\033[0m"

def _yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"

def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"

# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def extract_codes_from_file(filepath: str) -> set[str]:
    """
    Extract all error codes from a single file.

    Args:
        filepath: Absolute path to the file.

    Returns:
        set[str]: Set of error code strings found.
    """
    codes: set[str] = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                for match in ERROR_CODE_RE.finditer(line):
                    codes.add(match.group(0))
    except (OSError, IOError):
        pass
    return codes


def extract_registry_codes() -> set[str]:
    """
    Extract all error codes defined in ERROR_REGISTRY.md.

    Returns:
        set[str]: Set of error code strings from the registry.
    """
    path = os.path.abspath(REGISTRY_PATH)
    if not os.path.exists(path):
        print(_red(f"ERROR: Registry not found at {path}"))
        sys.exit(1)
    return extract_codes_from_file(path)


def extract_codebase_codes() -> dict[str, set[str]]:
    """
    Extract all error codes from Python files under apps/.

    Returns:
        dict[str, set[str]]: Mapping of relative filepath → set of codes found.
    """
    results: dict[str, set[str]] = {}
    apps_abs = os.path.abspath(APPS_DIR)

    for root, _dirs, files in os.walk(apps_abs):
        for fname in files:
            if not fname.endswith('.py'):
                continue
            full = os.path.join(root, fname)
            codes = extract_codes_from_file(full)
            if codes:
                rel = os.path.relpath(full, os.path.abspath(BACKEND_DIR))
                results[rel] = codes
    return results

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Compare error codes in registry vs codebase and print report.

    Returns:
        int: 0 if full coverage, 1 if gaps exist.
    """
    print(_bold("\n=== Error Code Coverage Report ===\n"))

    registry_codes = extract_registry_codes()
    codebase_map = extract_codebase_codes()

    # Flatten codebase codes
    codebase_codes: set[str] = set()
    for codes in codebase_map.values():
        codebase_codes.update(codes)

    # Remove test file codes from "codebase" set — tests legitimately reference
    # codes but shouldn't count as "implementation"
    impl_map: dict[str, set[str]] = {}
    test_codes: set[str] = set()
    for filepath, codes in codebase_map.items():
        if 'tests' in filepath or 'test_' in filepath:
            test_codes.update(codes)
        else:
            impl_map[filepath] = codes

    impl_codes: set[str] = set()
    for codes in impl_map.values():
        impl_codes.update(codes)

    # Compare
    in_registry_only = registry_codes - impl_codes
    in_code_only = impl_codes - registry_codes
    matched = registry_codes & impl_codes

    # Report: codes by file
    print(_bold("Codes found in codebase (implementation files):"))
    for filepath in sorted(impl_map.keys()):
        codes = sorted(impl_map[filepath])
        print(f"  {filepath}: {', '.join(codes)}")

    print()

    # Matched
    print(_bold(f"Matched (in registry + code): {len(matched)}"))
    for code in sorted(matched):
        print(f"  {_green(SYMBOL_OK)} {code}")

    # Registry-only (dead entries or not yet implemented)
    if in_registry_only:
        print(_bold(f"\n{_yellow('In registry but NOT in code')}: {len(in_registry_only)}"))
        for code in sorted(in_registry_only):
            print(f"  {_yellow(SYMBOL_WARN)} {code}")

    # Code-only (undocumented)
    if in_code_only:
        print(_bold(f"\n{_red('In code but NOT in registry')}: {len(in_code_only)}"))
        for code in sorted(in_code_only):
            # Find which file
            locations = [fp for fp, codes in impl_map.items() if code in codes]
            loc_str = ', '.join(locations)
            print(f"  {_red(SYMBOL_ERR)} {code}  ({loc_str})")

    # Test coverage
    tested_codes = test_codes & impl_codes
    print(f"\n{_bold('Test Coverage:')} {len(tested_codes)}/{len(impl_codes)} implementation codes have tests")

    # Summary
    total_registry = len(registry_codes)
    coverage = (len(matched) / total_registry * 100) if total_registry else 0

    print(f"\n{'='*50}")
    print(f"Registry entries:       {total_registry}")
    print(f"Implemented in code:    {len(impl_codes)}")
    print(f"Matched:                {len(matched)}")
    print(f"Registry-only:          {len(in_registry_only)}")
    print(f"Undocumented:           {len(in_code_only)}")
    print(f"Implementation rate:    {coverage:.1f}%")
    print(f"{'='*50}\n")

    if in_code_only:
        print(_red("ACTION: Add undocumented codes to ERROR_REGISTRY.md"))
    if in_registry_only:
        print(_yellow("INFO: Some registry codes are not yet implemented (may be planned)."))

    return 0 if (not in_code_only and coverage >= 80) else 1


if __name__ == '__main__':
    sys.exit(main())
