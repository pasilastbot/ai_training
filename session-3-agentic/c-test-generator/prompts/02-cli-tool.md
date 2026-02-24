# Prompt 02: Build Your CLI Tool

**When to use:** PART 1 — BUILD step
**Goal:** Build the coverage-check.sh script

---

```
@tools/coverage-check.sh.template

Complete the coverage checking script:

1. Run vitest with coverage (npx vitest run --coverage)
2. Parse the coverage output to extract the percentage
3. Compare against the threshold (default 80%)
4. Exit 0 if coverage meets threshold, exit 1 if below
5. Output which files are below threshold

Test it (it will show 0% since no tests exist yet):
  chmod +x tools/coverage-check.sh
  ./tools/coverage-check.sh 80
```

Note: You'll need vitest and coverage installed:
```bash
npm init -y
npm install -D vitest @vitest/coverage-v8
```

---

## What you should have after this step

- [ ] A working `coverage-check.sh` that runs tests and reports coverage
- [ ] Threshold comparison with exit codes
- [ ] Tool tested (shows 0% since no tests exist yet)
