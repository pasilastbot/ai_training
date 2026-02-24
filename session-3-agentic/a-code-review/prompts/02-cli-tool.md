# Prompt 02: Build Your CLI Tool

**When to use:** PART 1 — BUILD step
**Goal:** Build the check-security.sh script

---

```
@tools/check-security.sh.template

Complete the security checking script:

1. Scan files for these patterns using grep:
   - SQL injection: string concatenation in queries
   - Hardcoded secrets: API keys, passwords, tokens in source
   - Missing input validation: user input used without sanitization
   - Dangerous functions: eval(), exec(), innerHTML

2. For each finding, output JSON:
   { "type": "sql-injection", "file": "...", "line": 42, "match": "..." }

3. Exit 0 if no critical findings, exit 1 if any found
4. Accept a directory path as argument (default: current dir)

Test it against the sample diffs:
  chmod +x tools/check-security.sh
  ./tools/check-security.sh target/
```

---

## After building

Verify your tool works:

```bash
chmod +x tools/check-security.sh
./tools/check-security.sh target/
```

It should find issues in `sample-diff-1.patch` (SQL injection, hardcoded API key) and fewer issues in `sample-diff-2.patch`.

---

## What you should have after this step

- [ ] A working `check-security.sh` that scans for vulnerabilities
- [ ] JSON output format for findings
- [ ] Tool tested against sample diffs
