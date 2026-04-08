#!/usr/bin/env python3

from __future__ import annotations

import re
import shutil
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LANG_ROOT = SCRIPT_DIR / "lang"
USER_AGENT = "Mozilla/5.0"
DEFAULT_VERSION = "5.1"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_RETRIES = 2
DEFAULT_RETRY_DELAY_SECONDS = 1.5
DOWNLOAD_CHUNK_SIZE = 64 * 1024
LANGPACK_LIST_BASE_URL = "https://download.moodle.org/langpack"
LANGPACK_DOWNLOAD_BASE_URL = "https://download.moodle.org/download.php/direct/langpack"


def usage() -> None:
	print(
		"""Usage:
	./download.py [LANGCODE]
	./download.py --lang LANGCODE
	./download.py lang=LANGCODE
	./download.py lang LANGCODE
	./download.py --list
	./download.py --update
	./download.py [LANGCODE] [--version VERSION] [--timeout SECONDS] [--retries N] [--retry-delay SECONDS]
	./download.py --update [--version VERSION] [--timeout SECONDS] [--retries N] [--retry-delay SECONDS]

Downloads a Moodle language pack into ./lang/LANGCODE.

Options:
	--version VERSION	Moodle version for langpack URL (default: 5.1)
	--timeout SECONDS	Network timeout per request (default: 30)
	--retries N		Number of retries after the first failed request (default: 2)
	--retry-delay SECONDS	Delay between retries (default: 1.5)
	--update		Refresh already downloaded langpacks under ./lang/
"""
	)


def parse_positive_float(value: str, flag_name: str) -> float:
	try:
		parsed = float(value)
	except ValueError:
		print(f"Error: {flag_name} expects a number.", file=sys.stderr)
		raise SystemExit(1)

	if parsed <= 0:
		print(f"Error: {flag_name} must be greater than 0.", file=sys.stderr)
		raise SystemExit(1)

	return parsed


def parse_non_negative_int(value: str, flag_name: str) -> int:
	try:
		parsed = int(value)
	except ValueError:
		print(f"Error: {flag_name} expects an integer.", file=sys.stderr)
		raise SystemExit(1)

	if parsed < 0:
		print(f"Error: {flag_name} must be >= 0.", file=sys.stderr)
		raise SystemExit(1)

	return parsed


def parse_non_negative_float(value: str, flag_name: str) -> float:
	try:
		parsed = float(value)
	except ValueError:
		print(f"Error: {flag_name} expects a number.", file=sys.stderr)
		raise SystemExit(1)

	if parsed < 0:
		print(f"Error: {flag_name} must be >= 0.", file=sys.stderr)
		raise SystemExit(1)

	return parsed


def request_with_retries(url: str, timeout_seconds: float, retries: int, retry_delay_seconds: float) -> bytes:
	last_error: Exception | None = None

	for attempt in range(retries + 1):
		request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
		try:
			with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
				return response.read()
		except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
			last_error = exc
			if attempt < retries:
				print(
					f"Request failed (attempt {attempt + 1}/{retries + 1}), retrying in {retry_delay_seconds}s...",
					file=sys.stderr,
				)
				time.sleep(retry_delay_seconds)

	if last_error is None:
		last_error = RuntimeError("Unknown network error")
	raise last_error


def fetch_available_langs(version: str, timeout_seconds: float, retries: int, retry_delay_seconds: float) -> list[str]:
	list_url = f"{LANGPACK_LIST_BASE_URL}/{version}/"
	html = request_with_retries(list_url, timeout_seconds, retries, retry_delay_seconds).decode(
		"utf-8", errors="replace"
	)

	langs = sorted(set(re.findall(r"Download ([A-Za-z0-9_]+)\.zip", html)))
	return langs


def list_available_langs(available_langs: list[str]) -> None:
	print("Available language codes:")
	for code in available_langs:
		print(code)


def prompt_for_lang(available_langs: list[str]) -> str:
	list_available_langs(available_langs)
	return input("\nEnter the language code to download: ").strip()


def validate_lang(lang_code: str, available_langs: list[str]) -> None:
	if lang_code not in set(available_langs):
		print(
			f"Error: language code '{lang_code}' is not available in Moodle 2.0 langpacks.",
			file=sys.stderr,
		)
		print("Run './download.py --list' to see the current public list.", file=sys.stderr)
		raise SystemExit(1)


def download_archive(
	lang_code: str,
	archive_path: Path,
	version: str,
	timeout_seconds: float,
	retries: int,
	retry_delay_seconds: float,
) -> None:
	download_url = f"{LANGPACK_DOWNLOAD_BASE_URL}/{version}/{lang_code}.zip"
	last_error: Exception | None = None

	for attempt in range(retries + 1):
		request = urllib.request.Request(download_url, headers={"User-Agent": USER_AGENT})
		try:
			with urllib.request.urlopen(request, timeout=timeout_seconds) as response, archive_path.open("wb") as out_file:
				total_size = response.headers.get("Content-Length")
				total_bytes = int(total_size) if total_size and total_size.isdigit() else None
				downloaded = 0

				while True:
					chunk = response.read(DOWNLOAD_CHUNK_SIZE)
					if not chunk:
						break
					out_file.write(chunk)
					downloaded += len(chunk)

					if sys.stdout.isatty():
						if total_bytes and total_bytes > 0:
							percent = downloaded * 100.0 / total_bytes
							print(
								f"\rDownloading: {percent:6.2f}% ({downloaded}/{total_bytes} bytes)",
								end="",
								flush=True,
							)
						else:
							print(f"\rDownloading: {downloaded} bytes", end="", flush=True)

				if sys.stdout.isatty():
					print()

			with zipfile.ZipFile(archive_path) as zf:
				bad_file = zf.testzip()
				if bad_file is not None:
					raise zipfile.BadZipFile(f"Corrupt member: {bad_file}")
			return

		except (urllib.error.URLError, socket.timeout, TimeoutError, zipfile.BadZipFile) as exc:
			last_error = exc
			if archive_path.exists():
				archive_path.unlink(missing_ok=True)

			if attempt < retries:
				print(
					f"Download failed (attempt {attempt + 1}/{retries + 1}), retrying in {retry_delay_seconds}s...",
					file=sys.stderr,
				)
				time.sleep(retry_delay_seconds)

	print(f"Error: failed to download '{lang_code}' langpack.", file=sys.stderr)
	print(f"Tried URL: {download_url}", file=sys.stderr)
	if last_error is not None:
		print(f"Reason: {last_error}", file=sys.stderr)
	raise SystemExit(1)


def extract_langpack(lang_code: str, archive_path: Path, temp_extract_dir: Path) -> None:
	target_dir = LANG_ROOT / lang_code

	with zipfile.ZipFile(archive_path) as zf:
		zf.extractall(temp_extract_dir)

	top_level_entries = [entry for entry in temp_extract_dir.iterdir()]
	source_dir = temp_extract_dir
	if len(top_level_entries) == 1 and top_level_entries[0].is_dir():
		source_dir = top_level_entries[0]

	extracted_entries = [entry for entry in source_dir.iterdir()]
	if not extracted_entries:
		print(
			f"Error: zip archive for '{lang_code}' did not contain any files to extract.",
			file=sys.stderr,
		)
		raise SystemExit(1)

	if target_dir.exists():
		shutil.rmtree(target_dir)
	target_dir.mkdir(parents=True, exist_ok=True)

	for entry in extracted_entries:
		shutil.move(str(entry), target_dir / entry.name)


def find_installed_langs() -> list[str]:
	if not LANG_ROOT.exists():
		return []

	return sorted([entry.name for entry in LANG_ROOT.iterdir() if entry.is_dir()])


def parse_args(argv: list[str]) -> tuple[str, bool, bool, str, float, int, float]:
	lang_code = ""
	list_only = False
	update_only = False
	version = DEFAULT_VERSION
	timeout_seconds = DEFAULT_TIMEOUT_SECONDS
	retries = DEFAULT_RETRIES
	retry_delay_seconds = DEFAULT_RETRY_DELAY_SECONDS

	i = 0
	while i < len(argv):
		arg = argv[i]

		if arg == "--lang":
			if i + 1 >= len(argv):
				print("Error: --lang requires a value.", file=sys.stderr)
				usage()
				raise SystemExit(1)
			lang_code = argv[i + 1]
			i += 2
			continue

		if arg == "lang":
			if i + 1 >= len(argv):
				print("Error: lang requires a value.", file=sys.stderr)
				usage()
				raise SystemExit(1)
			lang_code = argv[i + 1]
			i += 2
			continue

		if arg.startswith("lang="):
			lang_code = arg.split("=", 1)[1]
			i += 1
			continue

		if arg.startswith("--lang="):
			lang_code = arg.split("=", 1)[1]
			i += 1
			continue

		if arg == "--list":
			list_only = True
			i += 1
			continue

		if arg == "--update":
			update_only = True
			i += 1
			continue

		if arg == "--version":
			if i + 1 >= len(argv):
				print("Error: --version requires a value.", file=sys.stderr)
				usage()
				raise SystemExit(1)
			version = argv[i + 1]
			i += 2
			continue

		if arg.startswith("--version="):
			version = arg.split("=", 1)[1]
			i += 1
			continue

		if arg == "--timeout":
			if i + 1 >= len(argv):
				print("Error: --timeout requires a value.", file=sys.stderr)
				usage()
				raise SystemExit(1)
			timeout_seconds = parse_positive_float(argv[i + 1], "--timeout")
			i += 2
			continue

		if arg.startswith("--timeout="):
			timeout_seconds = parse_positive_float(arg.split("=", 1)[1], "--timeout")
			i += 1
			continue

		if arg == "--retries":
			if i + 1 >= len(argv):
				print("Error: --retries requires a value.", file=sys.stderr)
				usage()
				raise SystemExit(1)
			retries = parse_non_negative_int(argv[i + 1], "--retries")
			i += 2
			continue

		if arg.startswith("--retries="):
			retries = parse_non_negative_int(arg.split("=", 1)[1], "--retries")
			i += 1
			continue

		if arg == "--retry-delay":
			if i + 1 >= len(argv):
				print("Error: --retry-delay requires a value.", file=sys.stderr)
				usage()
				raise SystemExit(1)
			retry_delay_seconds = parse_non_negative_float(argv[i + 1], "--retry-delay")
			i += 2
			continue

		if arg.startswith("--retry-delay="):
			retry_delay_seconds = parse_non_negative_float(arg.split("=", 1)[1], "--retry-delay")
			i += 1
			continue

		if arg in ("-h", "--help"):
			usage()
			raise SystemExit(0)

		if lang_code:
			print(f"Error: unexpected argument '{arg}'.", file=sys.stderr)
			usage()
			raise SystemExit(1)

		lang_code = arg
		i += 1

	if list_only and update_only:
		print("Error: --list and --update cannot be used together.", file=sys.stderr)
		usage()
		raise SystemExit(1)

	if update_only and lang_code:
		print("Error: --update cannot be combined with a language code.", file=sys.stderr)
		usage()
		raise SystemExit(1)

	return lang_code, list_only, update_only, version, timeout_seconds, retries, retry_delay_seconds


def main(argv: list[str]) -> int:
	lang_code, list_only, update_only, version, timeout_seconds, retries, retry_delay_seconds = parse_args(argv)

	try:
		available_langs = fetch_available_langs(version, timeout_seconds, retries, retry_delay_seconds)
	except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
		print("Error: could not fetch the list of available Moodle language packs.", file=sys.stderr)
		print(f"Reason: {exc}", file=sys.stderr)
		return 1

	if not available_langs:
		print("Error: could not fetch the list of available Moodle language packs.", file=sys.stderr)
		return 1

	if list_only:
		list_available_langs(available_langs)
		return 0

	if update_only:
		installed_langs = find_installed_langs()
		if not installed_langs:
			print(f"No installed langpacks found in {LANG_ROOT}.")
			return 0

		available_set = set(available_langs)
		updatable_langs = [code for code in installed_langs if code in available_set]
		skipped_langs = [code for code in installed_langs if code not in available_set]

		if skipped_langs:
			print("Skipping unknown langpacks (not in Moodle 2.0 list):")
			for code in skipped_langs:
				print(f"- {code}")

		if not updatable_langs:
			print("No installed langpacks can be updated from the current Moodle 2.0 list.")
			return 0

		failed: list[str] = []
		for code in updatable_langs:
			with tempfile.TemporaryDirectory() as tmp_dir_name:
				tmp_dir = Path(tmp_dir_name)
				archive_path = tmp_dir / f"{code}.zip"
				extract_dir = tmp_dir / "extracted"
				extract_dir.mkdir(parents=True, exist_ok=True)

				print(f"Refreshing Moodle langpack '{code}'...")
				try:
					download_archive(code, archive_path, version, timeout_seconds, retries, retry_delay_seconds)
					extract_langpack(code, archive_path, extract_dir)
				except SystemExit:
					failed.append(code)
					print(f"Failed: {code}", file=sys.stderr)
					continue

			print(f"Updated: {LANG_ROOT / code}")

		if failed:
			print("The following langpacks failed to update:", file=sys.stderr)
			for code in failed:
				print(f"- {code}", file=sys.stderr)
			return 1

		print(f"Done: refreshed {len(updatable_langs)} langpack(s).")
		return 0

	if not lang_code:
		lang_code = prompt_for_lang(available_langs)

	validate_lang(lang_code, available_langs)
	LANG_ROOT.mkdir(parents=True, exist_ok=True)

	with tempfile.TemporaryDirectory() as tmp_dir_name:
		tmp_dir = Path(tmp_dir_name)
		archive_path = tmp_dir / f"{lang_code}.zip"
		extract_dir = tmp_dir / "extracted"
		extract_dir.mkdir(parents=True, exist_ok=True)

		print(f"Downloading Moodle langpack '{lang_code}' (version {version})...")
		download_archive(lang_code, archive_path, version, timeout_seconds, retries, retry_delay_seconds)

		print(f"Extracting into {LANG_ROOT / lang_code}...")
		extract_langpack(lang_code, archive_path, extract_dir)

	print(f"Done: {LANG_ROOT / lang_code}")
	return 0


if __name__ == "__main__":
	try:
		raise SystemExit(main(sys.argv[1:]))
	except KeyboardInterrupt:
		print("\nInterrupted.", file=sys.stderr)
		raise SystemExit(130)
