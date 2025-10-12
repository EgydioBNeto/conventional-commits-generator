# Usage Guide

Comprehensive guide to all **Conventional Commits Generator** commands and features.

---

## Basic Command

### Interactive Commit

The most common way to use CCG is the interactive mode:

```bash
ccg
```

This starts the interactive prompt that guides you through creating a conventional commit.

---

## Command-Line Flags

CCG supports various flags to customize its behavior:

### `--commit`: Generate Message Only

Generate a commit message without actually creating a commit:

```bash
ccg --commit
```

**Use Cases**:

- Preview commit message format
- Test your commit message before committing
- Generate messages for documentation or examples

---

### `--push`: Push Without Committing

Push existing commits to remote without creating a new commit:

```bash
ccg --push
```

**Use Cases**:

- Push commits you've already created
- Retry a failed push
- Push to a new branch that doesn't exist remotely

**Features**:

- Automatically detects if branch exists on remote
- Offers to create remote branch with `--set-upstream` if needed
- Checks remote access before pushing

---

### `--edit`: Edit Existing Commits

Edit commit messages of existing commits:

```bash
ccg --edit
```

**Features**:

- Select from recent commits or enter commit hash
- Validates new message against conventional commits format
- Uses `git commit --amend` for latest commit (fast)
- Uses `git filter-branch` for older commits (rewrites history)
- Offers force push for commits already on remote

**Workflow**:

1. Choose how many recent commits to display
2. Select commit by number or hash
3. View current commit details
4. Enter new commit message and body
5. Review changes
6. Confirm edit
7. Optionally push with force flag

!!! danger "Warning: History Rewriting"

    Editing commits rewrites git history. If the commit has been pushed:

    - Force push will be required
    - May affect other collaborators
    - Should be avoided on shared branches (like `main`)

---

### `--delete`: Delete Existing Commits

Delete commits from history:

```bash
ccg --delete
```

**Features**:

- Interactive commit selection
- Shows full commit details before deletion
- Uses `git reset --hard HEAD~1` for latest commit
- Uses interactive rebase for older commits
- Requires explicit confirmation
- Offers force push for commits already on remote

**Workflow**:

1. Choose how many recent commits to display
2. Select commit by number or hash
3. View commit details
4. Confirm deletion (with warnings)
5. Commit is permanently removed
6. Optionally force push

!!! danger "Warning: Destructive Operation"

    Deleting commits is **irreversible**. Make sure you:

    - Have a backup if needed
    - Understand the impact on commit history
    - Coordinate with team members for shared branches
    - Use force push carefully

---

### `--tag`: Create and Push Tags

Create semantic version tags:

```bash
ccg --tag
```

**Features**:

- Validates tag format (Semantic Versioning)
- Supports annotated tags with messages
- Checks remote access before pushing
- Pushes tag to remote automatically

**Workflow**:

1. Enter tag name (validated against SemVer)
2. Choose between annotated or lightweight tag
3. Enter tag message (for annotated tags)
4. Confirm push to remote

!!! info "Semantic Versioning"

    CCG validates tags against [SemVer 2.0.0](https://semver.org/) specification:

    - `MAJOR.MINOR.PATCH`
    - Optional pre-release: `-alpha`, `-beta.1`
    - Optional build metadata: `+20250112`

---

### `--reset`: Discard Changes and Pull

Reset local changes and pull latest from remote:

```bash
ccg --reset
```

**Features**:

- Discards **all** uncommitted changes
- Removes untracked files
- Pulls latest from remote
- Requires explicit confirmation

**Workflow**:

1. Check for local changes
2. Show destructive warning
3. Require user confirmation
4. Discard changes with `git reset HEAD`, `git checkout .`, `git clean -fd`
5. Pull latest with `git pull`

!!! danger "Warning: Data Loss"

    This operation is **destructive** and **irreversible**:

    - All uncommitted changes are lost
    - Untracked files are deleted
    - Cannot be undone

---

### `--path`: Work with Specific Paths

Specify files, directories, or repository paths:

```bash
ccg --path <path1> [path2] [...]
```

**Two Modes**:

#### Mode 1: Change Working Directory

When providing a **single directory**, CCG changes to that directory and operates there:

```bash
ccg --path /path/to/another/repo
```

#### Mode 2: Stage Specific Files

When providing **multiple paths** or **files**, CCG stages only those paths:

```bash
ccg --path src/app.py tests/test_app.py
ccg --path src/ docs/
```

**Combined with Other Flags**:

```bash
# Edit commit in different repository
ccg --path /path/to/repo --edit

# Push from different repository
ccg --path /path/to/repo --push

# Create tag in specific repository
ccg --path /path/to/repo --tag
```

**Validation**:

- Paths must exist
- Paths must be within a git repository
- Invalid paths show helpful error messages

---

### `--version`: Show Version

Display CCG version information:

```bash
ccg --version
```

---

### `--help`: Show Help

Display usage information and available flags:

```bash
ccg --help
```

---

## Error Handling

CCG provides clear error messages for common issues:

### Not a Git Repository

```
✗ Not a git repository. Please initialize one with 'git init'.
```

**Solution**: Run `git init` or `cd` to a git repository.

---

### No Remote Configured

```
✗ No remote repository configured
```

**Solution**: Add a remote: `git remote add origin <url>`

---

### No Changes to Commit

```
✗ No changes to commit in the specified path(s). Make some changes before running the tool.
```

**Solution**: Make changes to files, then run CCG.

---

### Access Denied

```
✗ ACCESS DENIED: You don't have permission to access this repository.
✗ Please check:
   You have push access to this repository
   The repository URL is correct
   You're logged in with the correct account
```

**Solution**: Check your git credentials and repository permissions.
