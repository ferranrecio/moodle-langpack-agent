#!/usr/bin/env python3
"""
Find repeated string literals in Moodle langpacks.
Analyzes all PHP language files and identifies duplicate string values within each language.
Results are organized by language and show which keys share the same translation.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def extract_strings(php_file):
    """
    Extract string key-value pairs from a PHP language file.
    Returns a dict of {key: value} pairs.
    """
    strings = {}
    try:
        with open(php_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {php_file}: {e}")
        return strings

    # Match pattern: $string['key'] = 'value';
    # Handles escaped quotes and special characters
    pattern = r"\$string\['([^']+)'\]\s*=\s*'((?:[^'\\]|\\.)*)';"

    matches = re.findall(pattern, content)
    for key, value in matches:
        # Unescape the value
        value = value.replace("\\'", "'").replace("\\\\", "\\")
        strings[key] = value

    return strings

def find_repeated_in_language(lang_code):
    """
    Find repeated string values in a specific language.
    Returns a dict of {value: [list of keys]} for values that appear more than once.
    """
    lang_dir = Path('lang') / lang_code

    if not lang_dir.exists():
        return {}

    # Collect all strings from all PHP files in this language
    all_strings = {}
    file_count = 0

    for php_file in sorted(lang_dir.glob('*.php')):
        strings = extract_strings(php_file)
        all_strings.update(strings)
        if strings:
            file_count += 1

    # Find duplicates: values that appear in multiple keys
    value_to_keys = defaultdict(list)
    for key, value in all_strings.items():
        value_to_keys[value].append(key)

    # Keep only values that appear more than once
    repeated = {value: keys for value, keys in value_to_keys.items() if len(keys) > 1}

    return repeated, file_count, len(all_strings)

def main():
    """Main entry point."""
    lang_dir = Path('lang')

    if not lang_dir.exists():
        print("Error: 'lang' directory not found in current directory")
        return

    # Get all language folders
    languages = sorted([d.name for d in lang_dir.iterdir() if d.is_dir() and not d.name.startswith('info')])

    if not languages:
        print("No language folders found in lang/")
        return

    print(f"Found {len(languages)} language(s): {', '.join(languages)}\n")
    print("=" * 80)

    # Track statistics across all languages
    global_stats = {
        'total_strings': 0,
        'total_repeated_values': 0,
        'total_repeated_entries': 0,
        'languages_data': {}
    }

    for lang_code in languages:
        print(f"\n📚 Language: {lang_code.upper()}")
        print("-" * 80)

        repeated, file_count, total_strings = find_repeated_in_language(lang_code)

        # Count repeated entries (sum of all keys involved in repeated values)
        repeated_entries = sum(len(keys) for keys in repeated.values())

        # Store statistics
        global_stats['total_strings'] += total_strings
        global_stats['total_repeated_values'] += len(repeated)
        global_stats['total_repeated_entries'] += repeated_entries
        global_stats['languages_data'][lang_code] = {
            'total_strings': total_strings,
            'repeated_values': len(repeated),
            'repeated_entries': repeated_entries,
            'files': file_count
        }

        if not repeated:
            print(f"✓ No repeated strings found ({file_count} files, {total_strings} strings total)")
            continue

        repeated_pct = (repeated_entries / total_strings * 100) if total_strings > 0 else 0
        print(f"Found {len(repeated)} repeated string value(s) ({file_count} files, {total_strings} strings total):")
        print(f"   → {repeated_entries} entries involved in repetitions ({repeated_pct:.1f}% of total)\n")

        # Sort by frequency (most repeated first)
        sorted_repeated = sorted(repeated.items(), key=lambda x: len(x[1]), reverse=True)

        for value, keys in sorted_repeated:
            print(f"  Value: {repr(value)}")
            print(f"  Repeated {len(keys)} times in: {', '.join(sorted(keys))}")
            print()

    # Print global statistics
    print("=" * 80)
    print("\n📊 GLOBAL STATISTICS")
    print("=" * 80)
    print(f"\nTotal strings across all languages: {global_stats['total_strings']:,}")
    print(f"Total repeated values found: {global_stats['total_repeated_values']:,}")
    print(f"Total entries involved in repetitions: {global_stats['total_repeated_entries']:,}")

    if global_stats['total_strings'] > 0:
        percentage = (global_stats['total_repeated_entries'] / global_stats['total_strings'] * 100)
        print(f"\nRepetition rate: {percentage:.2f}% of all entries are repeated values")

    print("\nBreakdown by language:")
    print("-" * 80)
    for lang_code in languages:
        data = global_stats['languages_data'][lang_code]
        rate = (data['repeated_entries'] / data['total_strings'] * 100) if data['total_strings'] > 0 else 0
        print(f"  {lang_code.upper():3} | Strings: {data['total_strings']:6,} | Repeated values: {data['repeated_values']:5,} | Repeated entries: {data['repeated_entries']:6,} ({rate:5.2f}%)")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
