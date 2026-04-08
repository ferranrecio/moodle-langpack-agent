#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LANG_ROOT = SCRIPT_DIR / "lang"
PACK_ROOT = SCRIPT_DIR / "pack"

SECRET_KEY_NAME_RE = re.compile(
	r"\$string\['[^']*(?:api[_-]?key|secret|token|access[_-]?token|client[_-]?secret|password)[^']*'\]\s*=\s*'([^']+)'",
	re.IGNORECASE,
)

TOKEN_PATTERNS = [
	# Common provider token formats or strong token-like prefixes.
	re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
	re.compile(r"\b(?:sk|pk|rk)_[A-Za-z0-9]{16,}\b"),
	re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
	re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}\b"),
	re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
	re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
	# JWT-like values.
	re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
]


def _mask_preview(value: str) -> str:
	"""Create a safe preview for terminal output without exposing full secrets."""
	if len(value) <= 8:
		return value
	return f"{value[:4]}...{value[-4:]}"


def _looks_like_token(value: str) -> bool:
	"""Heuristic check for token-like values to avoid replacing normal text."""
	if value == "TOKENSAMPLE":
		return False

	if " " in value or "\t" in value or "\n" in value:
		return False

	for token_re in TOKEN_PATTERNS:
		if token_re.fullmatch(value):
			return True

	if len(value) < 20:
		return False

	has_lower = any(c.islower() for c in value)
	has_upper = any(c.isupper() for c in value)
	has_digit = any(c.isdigit() for c in value)
	has_symbol = any(c in "_-" for c in value)

	# Generic API key-like shape: long, compact, mixed classes.
	return has_digit and ((has_lower and has_upper) or has_symbol)


def sanitize_token_like_values(content: str, source_file: Path) -> tuple[str, list[str]]:
	"""Replace token-like values with TOKENSAMPLE and return replacement logs."""
	replacement_logs: list[str] = []

	def replace_secret_key_value(match: re.Match[str]) -> str:
		value = match.group(1)
		if not _looks_like_token(value):
			return match.group(0)

		line = content.count("\n", 0, match.start(1)) + 1
		replacement_logs.append(
			f"  - {source_file}:{line} key-value token { _mask_preview(value) } -> TOKENSAMPLE"
		)
		return match.group(0).replace(value, "TOKENSAMPLE", 1)

	sanitized = SECRET_KEY_NAME_RE.sub(replace_secret_key_value, content)

	for token_re in TOKEN_PATTERNS:
		def replace_token(match: re.Match[str]) -> str:
			value = match.group(0)
			if value == "TOKENSAMPLE":
				return value

			line = sanitized.count("\n", 0, match.start()) + 1
			replacement_logs.append(
				f"  - {source_file}:{line} token { _mask_preview(value) } -> TOKENSAMPLE"
			)
			return "TOKENSAMPLE"

		sanitized = token_re.sub(replace_token, sanitized)

	return sanitized, replacement_logs


def find_installed_langs() -> list[str]:
	"""Find all installed language directories in lang/"""
	if not LANG_ROOT.exists():
		return []

	return sorted([entry.name for entry in LANG_ROOT.iterdir() if entry.is_dir()])


def get_php_files(lang_dir: Path) -> list[Path]:
	"""Get all PHP files from a language directory, sorted by name"""
	php_files = sorted(lang_dir.glob("*.php"))
	return php_files


def create_markdown_for_lang(lang_code: str) -> str:
	"""Create markdown content for a language pack"""
	lang_dir = LANG_ROOT / lang_code

	if not lang_dir.exists():
		return ""

	# Start with level 1 title
	content = f"# Moodle {lang_code.upper()} langpack\n\n"

	# Get all PHP files
	php_files = get_php_files(lang_dir)

	if not php_files:
		content += "No PHP files found in this language pack.\n"
		return content

	# Process each PHP file
	for php_file in php_files:
		# Add level 2 title with filename
		content += f"## {php_file.name}\n\n"

		# Read and add file content
		try:
			with open(php_file, "r", encoding="utf-8") as f:
				file_content = f.read()
				safe_content, replacement_logs = sanitize_token_like_values(file_content, php_file)
				if replacement_logs:
					print(f"Replacements in {php_file}:")
					for log in replacement_logs:
						print(log)
				content += "```php\n"
				content += safe_content
				content += "\n```\n\n"
		except Exception as e:
			content += f"*Error reading file: {e}*\n\n"

	return content


def pack_langpacks() -> int:
	"""Pack all installed language packs into markdown files"""
	langs = find_installed_langs()

	if not langs:
		print("No installed language packs found in lang/")
		return 1

	PACK_ROOT.mkdir(parents=True, exist_ok=True)

	packed = 0
	for lang_code in langs:
		output_file = PACK_ROOT / f"langpack.{lang_code}.md"

		print(f"Creating markdown for '{lang_code}'...")

		try:
			markdown_content = create_markdown_for_lang(lang_code)

			with open(output_file, "w", encoding="utf-8") as f:
				f.write(markdown_content)

			print(f"✓ Created: {output_file}")
			packed += 1

		except Exception as e:
			print(f"✗ Error packing '{lang_code}': {e}", file=sys.stderr)

	print(f"\nDone: packed {packed} language pack(s).")
	return 0 if packed > 0 else 1


if __name__ == "__main__":
	try:
		raise SystemExit(pack_langpacks())
	except KeyboardInterrupt:
		print("\nInterrupted.", file=sys.stderr)
		raise SystemExit(130)
