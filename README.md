# Moodle Langpack Downloader

Small Python utility to download and refresh Moodle 2.0 language packs into the local `lang/` directory.

## What It Does

- Lists available Moodle 2.0 language pack codes.
- Downloads a specific language pack as a zip archive.
- Extracts files into `./lang/LANGCODE`.
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

Download Catalan:

```bash
./download.py ca
```

Download with custom network settings:

```bash
./download.py ca --timeout 20 --retries 4 --retry-delay 2
```

Refresh all installed packs:

```bash
./download.py --update
```

## Output Layout

- Download target: `./lang/LANGCODE`
- Existing destination folder is replaced when re-downloading/updating that language.

## Notes

- The script works with Moodle 2.0 langpack endpoints.
- During `--update`, local folders not present in the public Moodle 2.0 list are skipped.
