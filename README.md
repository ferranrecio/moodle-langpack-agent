# Moodle Langpack Downloader

Small Python utility to download and refresh Moodle 2.0 language packs into the local `lang/` directory.

## What It Does

- Lists available Moodle 2.0 language pack codes.
- Downloads a specific language pack as a zip archive.
- Extracts files into `./lang/LANGCODE`.
- Creates `./lang/info.LANGCODE.json` metadata after each successful download/update.
- Refreshes already installed language packs with `--update`.
- Retries failed network requests with configurable timeout and delay.

## Requirements

- Linux, macOS, or Windows
- Python 3.9+
- Internet access to `download.moodle.org`

No third-party dependencies are required.

## Quick Start

From the project root:

```bash
chmod +x download.py
./download.py --list
./download.py ca
```

Or run via Python explicitly:

```bash
python3 download.py --list
python3 download.py ca
```

## Run on macOS

Open Terminal and go to the project folder:

```bash
cd /path/to/moodle-langpack-agent
```

Check Python 3 is available:

```bash
python3 --version
```

Run the script (recommended):

```bash
python3 download.py --list
python3 download.py ca
```

Optional: make it directly executable and run it with `./`:

```bash
chmod +x download.py
./download.py --list
```

## Usage

```text
./download.py [LANGCODE]
./download.py --lang LANGCODE
./download.py lang=LANGCODE
./download.py lang LANGCODE
./download.py --list
./download.py --update
./download.py [LANGCODE] [--timeout SECONDS] [--retries N] [--retry-delay SECONDS]
./download.py --update [--timeout SECONDS] [--retries N] [--retry-delay SECONDS]
```

If no language code is provided, the script lists available codes and prompts interactively.

## Options

- `--version VERSION`: Moodle version for langpack URL. Default: `5.1`.
- `--list`: Print all currently available language codes.
- `--update`: Refresh every already-installed language under `./lang/`.
- `--timeout SECONDS`: Per-request timeout. Default: `30`.
- `--retries N`: Number of retries after the first failure. Default: `2`.
- `--retry-delay SECONDS`: Delay between retries. Default: `1.5`.
- `-h`, `--help`: Show usage help.

## Examples

List available packs:

```bash
./download.py --list
```

Download Catalan (default version 5.1):

```bash
./download.py ca
```

Download Catalan for Moodle 4.2:

```bash
./download.py ca --version 4.2
```

Download with custom network settings:

```bash
./download.py ca --timeout 20 --retries 4 --retry-delay 2
```

Refresh all installed packs with alternative version:

```bash
./download.py --update --version 5.1
```

## Output Layout

- Download target: `./lang/LANGCODE`
- Metadata file: `./lang/info.LANGCODE.json`
- Existing destination folder is replaced when re-downloading/updating that language.

### Metadata File Format

After a successful download (or `--update` refresh), the script writes a metadata file per language:

- Path pattern: `./lang/info.LANGCODE.json`
- Example for Catalan: `./lang/info.ca.json`

Fields:

- `lang`: language code that was downloaded.
- `moodle_version`: Moodle version used for the download URL.
- `downloaded_at`: local human-readable timestamp.
- `downloaded_at_iso`: ISO-8601 timestamp with timezone.

Example:

```json
{
	"lang": "ca",
	"moodle_version": "5.1",
	"downloaded_at": "April 08, 2026 16:22:11 CEST",
	"downloaded_at_iso": "2026-04-08T16:22:11.123456+02:00"
}
```

## Notes

- The script works with Moodle 2.0 langpack endpoints.
- During `--update`, local folders not present in the public Moodle 2.0 list are skipped.
