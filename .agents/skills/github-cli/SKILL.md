---
name: github-cli
description: Use for GitHub operations — pull requests, issues, releases, repos, workflows, and project tasks. Wraps the GitHub CLI (gh). Requires GitHub authentication.
---

## Command
`npm run github -- <subcommand> [options]`

## Subcommands

### auth
Manage GitHub authentication.

| Flag | Description |
|------|-------------|
| -l, --login | Log in to GitHub |
| -s, --status | View authentication status |
| -r, --refresh | Refresh stored credentials |
| -o, --logout | Log out of GitHub |

### pr-create
Create a pull request.

| Flag | Description |
|------|-------------|
| --title | PR title |
| --body | PR body |
| --base | Base branch name |
| --draft | Create as draft |
| --fill | Use commit info for title/body |

### pr-list
List pull requests.

| Flag | Description |
|------|-------------|
| --state | Filter: open, closed, merged, all (default: open) |
| --limit | Max items (default: 30) |
| --assignee | Filter by assignee |
| --author | Filter by author |
| --base | Filter by base branch |
| --web | Open in browser |

### pr-view
View PR details. Argument: `[number]` (PR number or URL).

| Flag | Description |
|------|-------------|
| --web | Open in browser |

### issue-create
Create a new issue.

| Flag | Description |
|------|-------------|
| --title | Issue title |
| --body | Issue body |
| --assignee | Assign by login |
| --label | Add labels |
| --project | Add to project |
| --milestone | Add to milestone |

### issue-list
List issues.

| Flag | Description |
|------|-------------|
| --state | Filter: open, closed, all (default: open) |
| --limit | Max items (default: 30) |
| --assignee | Filter by assignee |
| --label | Filter by label |

### release-create
Create a release. Argument: `<tag>`.

| Flag | Description |
|------|-------------|
| --title | Release title |
| --notes | Release notes |
| --notes-file | Read notes from file |
| --draft | Save as draft |
| --prerelease | Mark as prerelease |
| --generate-notes | Auto-generate notes |

### release-list
List releases.

| Flag | Description |
|------|-------------|
| --limit | Max items (default: 30) |

### repo
Manage repositories.

| Flag | Description |
|------|-------------|
| --create | Create new repository |
| --description | Repo description |
| --private | Make private |
| --view | View details |
| --list | List repositories |

### workflow
Manage GitHub workflows.

| Flag | Description |
|------|-------------|
| --list | List workflows |
| --run | Run a workflow |
| --view | View a workflow |
| --enable | Enable a workflow |
| --disable | Disable a workflow |

### tasks
List tasks from GitHub Projects and Issues.

| Flag | Description |
|------|-------------|
| --project | Project ID or number |
| --repository | Repo in owner/repo format |
| --status | Filter: open, closed, all |
| --label | Filter by label |
| --format | Output: table, json, simple |

## Requirements
- GitHub CLI (`gh`) — auto-installed if missing
- GitHub account authentication

## Examples
```bash
# Create a PR
npm run github -- pr-create --title "New feature" --body "Adds X"

# List open PRs
npm run github -- pr-list

# Create an issue
npm run github -- issue-create --title "Bug report" --label bug

# List tasks
npm run github -- tasks --format json
```
