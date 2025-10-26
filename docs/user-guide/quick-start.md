# Quick Start Guide

Get up and running with **Conventional Commits Generator** in minutes!

---

## Prerequisites

Make sure you have:

- [Installed CCG](installation.md)
- A Git repository to work with
- Some uncommitted changes ready to commit

---

## Your First Commit

Let's create your first conventional commit step by step.

### 1. Navigate to Your Repository

```bash
cd /path/to/your/git/repository
```

### 2. Make Some Changes

```bash
# Example: modify a file
echo "# New feature" >> README.md
```

### 3. Run CCG

```bash
ccg
```

You'll see the CCG logo and repository information:

```
 ________      ________      ________
|\   ____\    |\   ____\    |\   ____\
\ \  \___|    \ \  \___|    \ \  \___|
 \ \  \        \ \  \        \ \  \  ___
  \ \  \____    \ \  \____    \ \  \|\  \
   \ \_______\   \ \_______\   \ \_______\
    \|_______|    \|_______|    \|_______|

 Conventional Commits Generator

Repository: my-project  Branch: main
```

---

## Interactive Prompts

CCG will guide you through a series of prompts:

### Step 1: Choose Commit Type

```
┌──────────────────────┐
│ Commit Types         │
└──────────────────────┘

1. ✨ feat     - A new feature
2. 🐛 fix      - A bug fix
3. 🔧 chore    - Maintenance tasks
4. 🔨 refactor - Code refactoring
5. 💄 style    - Style changes
6. 📚 docs     - Documentation
7. 🧪 test     - Adding or modifying tests
8. 📦 build    - Build system changes
9. ⏪ revert   - Reverts a previous commit
10. 👷 ci      - CI/CD changes
11. ⚡ perf    - Performance improvements

Choose the commit type (number or name):
```

!!! tip "Pro Tip"
    You can type the number (e.g., `1`) or the name (e.g., `feat`)

**Example**: Let's choose `1` for a new feature.

---

### Step 2: Enter Scope (Optional)

```
┌──────────────────────┐
│ Scope                │
└──────────────────────┘
ℹ The scope provides context for the commit (e.g., module or file name)
ℹ Examples: auth, ui, api, database

Enter the scope (optional, press Enter to skip):
```

**Example**: Let's type `docs` to indicate this change affects documentation.

---

### Step 3: Breaking Change

```
┌──────────────────────┐
│ Breaking Change      │
└──────────────────────┘
ℹ A breaking change means this commit includes incompatible changes
ℹ Examples: changing function signatures, removing features, etc.

Is this a BREAKING CHANGE? (y/n):
```

**Example**: Let's type `n` since this is not a breaking change.

---

### Step 4: Include Emoji

```
┌──────────────────────┐
│ Emoji                │
└──────────────────────┘
ℹ GitHub-compatible emojis can make your commits more visual and expressive
ℹ Examples: :sparkles: feat, :bug: fix, :books: docs

Include emoji in commit message? (y/n):
```

**Example**: Let's type `y` to include emojis.

---

### Step 5: Commit Message

```
┌──────────────────────┐
│ Commit Message       │
└──────────────────────┘
ℹ Provide a clear, concise description of the change
ℹ Examples: 'implement OAuth login', 'fix navigation bug', 'update documentation'

Enter the commit message:
```

**Example**: Let's type `add installation guide`.

---

### Step 6: Commit Body (Optional)

```
┌──────────────────────┐
│ Commit Body          │
└──────────────────────┘
ℹ Add implementation details, breaking changes, or issue references (optional)
ℹ Examples: 'Added Google OAuth integration', 'BREAKING: API endpoint changed', 'Fixes #123'

Commit body (optional):
```

**Example**: Let's add more details:

```
Detailed installation instructions for pipx, pip, and development setup.
Includes troubleshooting section.
```

!!! info "Multiline Input"

    For commit body, you can:

    - **With prompt_toolkit**: Press Enter for new lines, Ctrl+D to finish
    - **Without prompt_toolkit**: Press Enter twice (empty line) to finish

---

### Step 7: Review

```
┌──────────────────────┐
│ Review               │
└──────────────────────┘
Commit: 📚 docs(docs): add installation guide

Body:
Detailed installation instructions for pipx, pip, and development setup.
Includes troubleshooting section.

Confirm this commit message? (Y/n):
```

**Example**: Type `y` to confirm.

---

### Step 8: Push Changes

```
✅ Commit message confirmed!

┌──────────────────────┐
│ Git Staging          │
└──────────────────────┘
→ Staging changes for .
✅ Changes staged successfully

┌──────────────────────┐
│ Commit               │
└──────────────────────┘
→ Committing changes...
✅ New commit successfully created!

┌──────────────────────┐
│ Push Changes         │
└──────────────────────┘
ℹ This will execute 'git push' command

Do you want to push these changes? (Y/n):
```

**Example**: Type `y` to push to remote, or `n` to keep changes local.

---

## Understanding the Result

After completion, your commit is created following the **Conventional Commits** specification:

```
:books: docs(docs): add installation guide

Detailed installation instructions for pipx, pip, and development setup.
Includes troubleshooting section.

Co-Authored-By: Agent <noreply@agent.com>
```

### Commit Format Breakdown

```
<emoji> <type>(<scope>): <description>

<body>

<footer>
```

- **Emoji** (optional): Visual indicator (`:books:` → 📚)
- **Type**: Category of change (`docs`)
- **Scope** (optional): Area affected (`docs`)
- **Description**: Brief summary (`add installation guide`)
- **Body** (optional): Detailed explanation
- **Footer** (optional): Breaking changes, issues, co-authors

---

## Common Workflows

### Quick Commit (No Body)

For simple changes, skip the body:

```bash
ccg
# Choose type: 2 (fix)
# Scope: [press Enter to skip]
# Breaking change: n
# Include emoji: y
# Message: resolve login redirect issue
# Body: [press Enter to skip]
# Confirm: y
# Push: y
```

Result: `:bug: fix: resolve login redirect issue`

---

### Feature with Breaking Change

For major changes:

```bash
ccg
# Choose type: 1 (feat)
# Scope: api
# Breaking change: y  ← Important!
# Include emoji: y
# Message: redesign authentication flow
# Body: BREAKING: Changed /auth endpoint to use JWT tokens
# Confirm: y
# Push: y
```

Result: `:sparkles: feat(api)!: redesign authentication flow`

---

### Verify Commit Compliance

Check if your commits follow the Conventional Commits standard:

```bash
ccg --analyze
# Choose how many commits to check (or press Enter for all)
# View color-coded results (✓ valid, ✗ invalid)
# Use the commit numbers shown to fix invalid commits with --edit
```

**Example Output**:

```
1. ✓ [a3c6dbc] feat(ux): improvements in usability
2. ✗ [2812ed3] update bump version workflow
3. ✓ [fa6a6df] feat: adding improvements
```

!!! tip "When to Use"
    - After adopting Conventional Commits in an existing project
    - Before creating a release
    - To identify which commits need fixing

---

## Important Notes

!!! warning "Git Repository Required"
    CCG must be run inside a Git repository. If you see "Not a git repository" error, run `git init` first.

!!! info "Pre-commit Hooks"
    If your repository has `.pre-commit-config.yaml`, CCG will automatically:

    - Install pre-commit hooks
    - Run hooks on staged files
    - Abort commit if hooks fail

!!! tip "Remote Access"
    CCG checks remote repository access before operations. Ensure you have:

    - Configured remote (`git remote add origin <url>`)
    - Proper authentication (SSH keys or HTTPS credentials)
    - Push permissions

---

## Troubleshooting

### No Changes to Commit

**Problem**: "No changes to commit" error

**Solution**: Make sure you have uncommitted changes:

```bash
git status  # Check for modified files
```

---

### Permission Denied

**Problem**: Can't push to remote

**Solution**: Check your git credentials:

```bash
git remote -v  # Verify remote URL
ssh -T git@github.com  # Test SSH (for SSH URLs)
```

---

### Pre-commit Hooks Failed

**Problem**: Commit aborted due to hook failures

**Solution**: Fix the issues reported by pre-commit:

```bash
pre-commit run --all-files  # See what's failing
# Fix the issues, then run ccg again
```

---

### Debug with Verbose Mode

**Problem**: Something isn't working as expected

**Solution**: Use verbose mode to see detailed logs:

```bash
ccg --verbose
# or
ccg -v
```

This enables debug output showing:

- All git commands being executed
- Detailed error messages
- Step-by-step operation flow

**Log File**: Check `~/.ccg/ccg.log` for the complete log history.

---

## Congratulations!

You've successfully created your first conventional commit with CCG!

Continue exploring the documentation to become a conventional commits expert.
