# Exercise 1: Invent a Tool

**Duration:** 10 min | **Type:** Build

---

## Goal

Use the AGENTS.md "invent" workflow to create a new CLI tool from a single prompt.

---

## The Workflow

The `invent` workflow in AGENTS.md instructs the AI to:

1. **Implement** — Write the CLI tool based on your description
2. **Test** — Generate and run tests to verify it works
3. **Document** — Create usage docs and register the tool

---

## The Prompt

Open your AI assistant (Cursor, Claude Code, etc.) and enter:

```
Invent a new tool: [your tool description]
```

That's it. The AI handles implementation, testing, and documentation.

---

## Tool Ideas

Choose one or invent your own:

| Tool | Description |
|------|-------------|
| **git-summary** | Summarize git commits since last release |
| **link-checker** | Check for broken links in markdown files |
| **dep-graph** | Generate a dependency graph for a project |
| **api-health** | Monitor API response times |
| **log-analyzer** | Parse and summarize log files |
| **pr-summarizer** | Generate a summary of a GitHub PR |
| **slack-notify** | Send notifications to a Slack channel |
| **db-health** | Check database connection and query performance |

---

## Example Prompt

```
Invent a new tool: A CLI that checks for broken links in all markdown 
files in a directory. It should report which files have broken links 
and what those links are. Output should be human-readable.
```

---

## What to Observe

As the AI builds your tool, watch for:

- **Planning** — Does it break down the task before coding?
- **Implementation** — Does it follow good patterns?
- **Testing** — Does it write and run tests?
- **Documentation** — Does it explain how to use the tool?

---

## Checkpoint

After 10 minutes:

- [ ] Tool is implemented
- [ ] Tests pass (or at least exist)
- [ ] You can run the tool from command line
- [ ] You understand what the tool does

---

## Keep Your Tool

Save your tool — you'll integrate it into your agent in Exercise 3.
