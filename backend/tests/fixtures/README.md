# Import fixtures

Every value in these files is invented, including the business names and the phone numbers —
AGENTS.md non-negotiable 4: real lead data never enters git. They mirror the real research
list's 16 columns and its CRLF line endings, so the importer's tests exercise the same shape
the real export has.

**No test may read `data/`.** That directory is gitignored, so a test that reads the real list
would pass on the machine that has it and fail in CI.

| Fixture | What it is there to produce |
|---|---|
| `import_clean.csv` | 3 rows, all good: 3 accepted, 0 rejected, 0 warnings |
| `import_mixed.csv` | 7 rows: 3 accepted, 4 rejected (one of each refusal), 1 warning |
| `import_duplicate_of_existing.csv` | 1 row, refused once its phone already exists on a lead |
| `import_missing_column.csv` | The header is missing a column we read, so the file is refused |
| `import_header_only.csv` | 0 data rows: 0 accepted, 0 rejected |
| `import_not_utf8.csv` | Not valid UTF-8, so the file is refused |
