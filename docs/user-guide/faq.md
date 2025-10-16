# Frequently Asked Questions

Common questions and troubleshooting for CCG users.

---

## General Questions

### What is Conventional Commits?

Conventional Commits is a specification for adding human and machine-readable meaning to commit messages. It provides a lightweight convention for commit history that makes it easier to write automated tools.

Learn more at [conventionalcommits.org](https://www.conventionalcommits.org/).

---

### Why should I use CCG?

**Benefits**:

- **Consistency**: Standardized commits across your team
- **Clarity**: Clear commit messages make code review easier
- **Safety**: Built-in validation and confirmation prompts

---

### Does CCG work with GitHub/GitLab/Bitbucket?

Yes! CCG is a git tool that works with any git hosting platform including GitHub, GitLab, Bitbucket, Azure DevOps, and self-hosted git servers.

---

## Installation & Setup

### Can I use CCG without pipx?

Yes, you can install with pip:

```bash
pip install conventional-commits-generator
```

However, pipx is recommended to avoid dependency conflicts.

---

### How do I update CCG?

=== "pipx"

   ```bash
   pipx upgrade conventional-commits-generator
   ```

=== "pip"

   ```bash
   pip install --upgrade conventional-commits-generator
   ```

---

### Does CCG require specific Python version?

CCG requires **Python 3.9 or higher**. Check your version:

```bash
python3 --version
```

---

## Usage Questions

### Can I use CCG without push access?

Yes! You can use CCG to create commits locally. When asked to push, simply answer "no".

---

### How do I skip the body?

Just press **CTRL + D** when prompted for the commit body. The body is optional.

---

### Can I edit a commit I already pushed?

Yes, use `ccg --edit`. However, this requires force pushing and can affect collaborators.

!!! warning
    Editing pushed commits rewrites history. Coordinate with your team.

---

### Can I delete multiple commits at once?

No, CCG deletes one commit at a time for safety. Run `ccg --delete` multiple times if needed.

---

### Does CCG support merge commits?

CCG focuses on regular commits. For merges, use standard git commands:

```bash
git merge feature-branch
# or
git merge --no-ff feature-branch
```

---

## Troubleshooting

### "Command not found: ccg"

**Cause**: CCG is not in your PATH.

**Solutions**:

1. **Ensure pipx path is configured**:

   ```bash
   pipx ensurepath
   source ~/.bashrc  # or ~/.zshrc
   ```

2. **Check installation**:

   ```bash
   pipx list  # Should show conventional-commits-generator
   ```

3. **Reinstall**:

   ```bash
   pipx install --force conventional-commits-generator
   ```

---

### "Not a git repository"

**Cause**: Current directory is not a git repository.

**Solution**:

```bash
# Initialize git
git init

# Or navigate to a git repository
cd /path/to/your/repo
```

---

### "No remote repository configured"

**Cause**: Git repository has no remote.

**Solution**:

```bash
git remote add origin <repository-url>
```

---

### "Permission denied" when pushing

**Cause**: Authentication or permission issues.

**Solutions**:

1. **Check repository URL**:

   ```bash
   git remote -v
   ```

2. **Test SSH access** (for SSH URLs):

   ```bash
   ssh -T git@github.com
   ```

3. **Verify permissions**: Ensure you have write access to the repository.

4. **Update credentials**: Reconfigure git credentials.

---

### "Pre-commit checks failed"

**Cause**: Pre-commit hooks detected issues.

**Solution**:

1. **Review failed checks**:

   ```bash
   pre-commit run --all-files
   ```

2. **Fix reported issues**

3. **Run CCG again**:

   ```bash
   ccg
   ```

---

### Input/Output encoding errors

**Cause**: Terminal encoding issues (rare).

**Solution**:

```bash
export PYTHONIOENCODING=utf-8
ccg
```

---

### How do I debug issues?

**Solution**: Use verbose mode to see detailed logs:

```bash
ccg --verbose
# or
ccg -v
```

**What verbose mode shows**:

- All git commands executed
- Detailed error messages
- Step-by-step operation flow
- Timestamps for all operations

**Log file location**:

- Linux/Mac: `~/.ccg/ccg.log`
- Windows: `%USERPROFILE%\.ccg\ccg.log`

**When to use verbose mode**:

- Debugging authentication issues
- Understanding unexpected behavior
- Reporting bugs (include logs)
- Troubleshooting pre-commit hooks

---

## Features & Behavior

### Can I customize commit types?

Currently, CCG uses standard conventional commit types. Custom types are not supported but may be added in future versions.

---

### Does CCG support co-authors?

Yes! Add co-authors in the commit body:

```
Co-authored-by: Name <email@example.com>
Co-authored-by: Another Name <another@example.com>
```

CCG automatically adds itself as a co-author.

---

### Can I disable emoji?

Yes, answer "no" when prompted "Include emoji in commit message?".

---

### Does CCG work offline?

Yes, for local operations (commit, edit, delete). Push operations require internet connectivity.

---

### Can I use CCG in scripts?

CCG is interactive by design. For scripted commits, use standard git:

```bash
git commit -m "feat: automated commit"
```

---

## Integration & Compatibility

### Works with pre-commit?

Yes! CCG automatically detects and runs pre-commit hooks if `.pre-commit-config.yaml` exists.

---

### IDE/Editor Integration

CCG is a CLI tool. Run it in your IDE's integrated terminal:

- **VS Code**: Terminal panel (Ctrl+\`)
- **PyCharm**: Terminal tool window
- **Vim/Neovim**: `:terminal` command
- **Emacs**: `M-x shell`

---

## Performance & Limits

### How many commits can CCG show?

By default, CCG shows recent commits. When editing/deleting, you choose how many to display (or "all").

---

### Is there a message length limit?

Yes, for user experience:

- **Type**: 8 characters
- **Scope**: 16 characters
- **Message**: 64 characters
- **Body**: 512 characters
- **Tag**: 32 characters

These are soft limits enforced by the input validator.

---

## Error Messages

### "Failed to get remote name"

**Cause**: No git remote configured.

**Solution**:

```bash
git remote add origin <url>
```

---

### "Commit validation failed"

**Cause**: Message doesn't follow conventional commit format.

**Solution**: Ensure format is: `type(scope): description`

Valid examples:

```
feat: add feature
fix(auth): resolve bug
docs(api)!: breaking docs change
```

---

### "Filter-branch failed"

**Cause**: Git operation failed during history rewriting.

**Solution**:

1. Check for conflicting git operations
2. Ensure clean working directory
3. Try again or use manual git commands

---

## Best Practices

### Should I always include emoji?

**Personal preference**. Emoji provides visual cues but isn't required by the specification.

**Pros**:

- Easy to scan commit history
- Color-coded by type
- GitHub renders them nicely

**Cons**:

- Some tools don't render emoji
- Not part of official spec
- Slightly longer messages

---

### How detailed should commit bodies be?

Include enough context for future developers (including yourself) to understand:

- **What** changed (briefly, details in code)
- **Why** it changed (motivation)
- **How** it affects users (if applicable)
- **References** to issues/docs

---

### Should I edit commits before PR?

**Yes**, if commits are:

- Poorly worded
- Missing important context
- Not following conventions
- WIP or debug commits

**No**, if:

- Commits are clear and follow conventions
- They accurately represent development history

---

## Getting Help

### Where can I report bugs?

Report bugs on GitHub:
[issues](https://github.com/EgydioBNeto/conventional-commits-generator/issues)

---

### How do I request features?

Create a feature request [issue](https://github.com/EgydioBNeto/conventional-commits-generator/issues) on GitHub with:

- Clear description
- Use cases
- Examples

---

### Where can I find more help?

- **Documentation**: [Full User Guide](installation.md)
- **Security**: [Security policy](../community/security.md)
- **Contributing**: [Contribution guidelines](../community/contributing.md)
