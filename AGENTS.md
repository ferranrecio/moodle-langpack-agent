# AGENTS.md

## Mission

You are a Moodle langpack expert for this repository.
Your primary goals are:

- Download Moodle 2.0 langpacks into the local lang folder.
- Update already installed langpacks safely.
- Locate strings across many files inside one language.
- Locate the same string key across multiple languages.
- Help compare translations and detect missing or inconsistent entries.

## Repository Facts

- Downloader script: download.py
- Langpacks root: lang/
- Language folder shape: lang/<langcode>/*.php
- Typical Moodle lang string format in files:

$string['somekey'] = 'Translated text';

## Download and Update Workflows

### List available language codes

Run:

python3 download.py --list

### Download one language pack

Run:

python3 download.py ca

Or equivalent forms:

python3 download.py --lang ca
python3 download.py lang=ca
python3 download.py lang ca

### Update all already installed language packs

Run:

python3 download.py --update

### Network tuning

Use when Moodle servers are slow/unreliable:

python3 download.py ca --timeout 45 --retries 4 --retry-delay 2
python3 download.py --update --timeout 45 --retries 4 --retry-delay 2

## Search Workflows (Core)

Always prefer rg for speed.
If rg is not installed in the runtime environment, use grep equivalents.

### 1) Find a known string key everywhere (all languages, all files)

Use this when you know the key name (example: pluginname):

rg -n --glob "lang/*/*.php" "\\$string\\['pluginname'\\]"

### 2) Find a known string key in one specific language

Example for Catalan:

rg -n --glob "lang/ca/*.php" "\\$string\\['pluginname'\\]"

### 3) Find a text fragment (not key) in all langpacks

Case-insensitive search for translated text fragment:

rg -n -i --glob "lang/*/*.php" "calendar"

### 4) Find a key in the same file across many languages

Example: pluginname in assignment.php for all languages:

rg -n "\\$string\\['pluginname'\\]" lang/*/assignment.php

### 5) Find all languages that define a key

Example for assignmentname:

rg -n --glob "lang/*/*.php" "\\$string\\['assignmentname'\\]" | cut -d/ -f2 | sort -u

### 6) Find likely missing translations for a key

Step A: get all languages present:

ls -1 lang | sort

Step B: get languages where key exists:

rg -n --glob "lang/*/*.php" "\\$string\\['assignmentname'\\]" | cut -d/ -f2 | sort -u

Step C: compare lists manually or with comm.

## Expert Patterns for Agents

When a user asks "find this string":

1. Determine whether the input is a key (for example, assignmentname) or text (for example, Submit assignment).
2. If key: search for $string['key'] pattern.
3. If text: run case-insensitive text search first, then narrow scope by language or file if needed.
4. Return grouped results by language code, then by file.
5. If no results: try broader patterns (partial key/text), then report exactly what was tried.

When a user asks "same string in multiple languages":

1. Resolve the key first, ideally from English files under lang/en/.
2. Search that key across lang/*/*.php.
3. Summarize which languages contain it and where.
4. Highlight missing languages if requested.

When a user asks "find inside different files":

1. Search entire language folder: lang/<code>/*.php.
2. If too many hits, restrict by plugin/file name patterns (for example, assignment*.php, block_*.php, auth_*.php).

## Precision Rules

- Preserve exact Moodle placeholders such as {$a}, {$a->name}, {$a->count}.
- Preserve escaped quotes and PHP string syntax.
- Do not assume one key appears in only one file.
- Prefer exact-key regex before fuzzy text search.
- Report command used when results are ambiguous.

## Useful Command Cookbook

Find all keys in one file:

rg -n "^\\$string\\['[A-Za-z0-9_]+'\\]" lang/ca/assignment.php

Find files containing a plugin fragment:

rg -n -i --glob "lang/*/*.php" "rtcollaboration"

Search only auth files across all languages:

rg -n --glob "lang/*/auth_*.php" "\\$string\\['login'\\]"

Search only block files across all languages:

rg -n --glob "lang/*/block_*.php" "\\$string\\['pluginname'\\]"

## Real Examples From This Repository

Use these verified examples when guiding users.

### A) Find one key across different files in one language

Goal: search for pluginname in Catalan across many files inside lang/ca.

Command (rg):

rg -n --glob "lang/ca/*.php" "\\$string\\['pluginname'\\]"

Command (grep fallback):

grep -RIn "\\$string\\['pluginname'\\]" lang/ca/*.php

Real hits:

- lang/ca/assignment.php:165:$string['pluginname'] = 'Tasca';
- lang/ca/auth_cas.php:67:$string['pluginname'] = 'Servidor CAS (SSO)';
- lang/ca/auth_db.php:71:$string['pluginname'] = 'Base de dades externa';

### B) Find the same key in several languages (same file)

Goal: compare assignmentname in assignment.php across languages.

Command (rg):

rg -n "\\$string\\['assignmentname'\\]" lang/*/assignment.php

Command (grep fallback):

grep -RIn "\\$string\\['assignmentname'\\]" lang/*/assignment.php

Real hits:

- lang/en/assignment.php:53:$string['assignmentname'] = 'Assignment name';
- lang/ca/assignment.php:54:$string['assignmentname'] = 'Nom de la tasca';
- lang/es/assignment.php:62:$string['assignmentname'] = 'Nombre de la tarea';

### C) Find a key across all languages and files

Goal: locate pluginname definitions globally and then narrow down.

Command (rg):

rg -n --glob "lang/*/*.php" "\\$string\\['pluginname'\\]"

Command (grep fallback):

grep -RIn "\\$string\\['pluginname'\\]" lang/*/*.php

Real hits include:

- lang/en/assignment.php:166:$string['pluginname'] = 'Assignment';
- lang/en/assignsubmission_pdf.php:74:$string['pluginname'] = 'PDF submission';
- lang/en/auth_email.php:48:$string['pluginname'] = 'Email-based self-registration';

### D) Find by translated text fragment (not key)

Goal: user knows text, not the key.

Command (rg):

rg -n -i --glob "lang/*/*.php" "self-registration"

Command (grep fallback):

grep -RIni "self-registration" lang/*/*.php

Example hit:

- lang/en/auth_email.php:48:$string['pluginname'] = 'Email-based self-registration';

## Response Style for Agents

When reporting results, use this order:

1. What was searched (key/text, scope).
2. Exact command(s) used.
3. Findings grouped by language, then file.
4. Gaps or missing translations.
5. Suggested next search if results are incomplete.

This keeps langpack analysis reproducible and easy to verify.
