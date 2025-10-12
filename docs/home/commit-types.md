# Commit Types

CCG supports all standard conventional commit types with clear descriptions and optional emoji support.

---

## Available Types

| Type       | Description                   | Emoji |
| ---------- | ----------------------------- | ----- |
| `feat`     | A new feature                 | ✨    |
| `fix`      | A bug fix                     | 🐛    |
| `docs`     | Documentation changes         | 📚    |
| `style`    | Code style/formatting changes | 💄    |
| `refactor` | Code refactoring              | 🔨    |
| `test`     | Adding or modifying tests     | 🧪    |
| `chore`    | Maintenance tasks             | 🔧    |
| `perf`     | Performance improvements      | ⚡    |
| `ci`       | CI/CD changes                 | 👷    |
| `build`    | Build system changes          | 📦    |
| `revert`   | Reverts a previous commit     | ⏪    |

---

## Detailed Descriptions

### `feat` - New Features

Use `feat` when you add a new feature or capability to the codebase.

**Examples:**

```
feat: add user authentication
feat(api): implement OAuth2 login
feat!: redesign navigation system (breaking change)
```

---

### `fix` - Bug Fixes

Use `fix` when you repair a bug or issue in the code.

**Examples:**

```
fix: resolve memory leak in data processing
fix(ui): correct button alignment on mobile
fix: handle null pointer exception in validator
```

---

### `docs` - Documentation

Use `docs` for documentation-only changes (no code changes).

**Examples:**

```
docs: update installation instructions
docs(api): add examples to README
docs: fix typos in contributing guide
```

---

### `style` - Code Style

Use `style` for formatting changes that don't affect code behavior (whitespace, semicolons, etc.).

**Examples:**

```
style: format code with black
style: fix indentation in utils module
style: remove trailing whitespace
```

---

### `refactor` - Code Refactoring

Use `refactor` when you restructure code without changing its external behavior.

**Examples:**

```
refactor: extract validation logic to separate class
refactor(db): optimize query performance
refactor: simplify error handling
```

---

### `test` - Tests

Use `test` when adding, modifying, or fixing tests.

**Examples:**

```
test: add unit tests for authentication
test(api): increase coverage to 100%
test: fix flaky integration test
```

---

### `chore` - Maintenance

Use `chore` for maintenance tasks, dependency updates, and other housekeeping.

**Examples:**

```
chore: update dependencies
chore: bump version to 2.3.0
chore(deps): upgrade pytest to 7.4.0
```

---

### `perf` - Performance

Use `perf` for performance improvements.

**Examples:**

```
perf: optimize database queries
perf(cache): implement Redis caching
perf: reduce bundle size by 30%
```

---

### `ci` - Continuous Integration

Use `ci` for CI/CD configuration and pipeline changes.

**Examples:**

```
ci: add GitHub Actions workflow
ci: update test matrix to include Python 3.13
ci: configure automated releases
```

---

### `build` - Build System

Use `build` for changes to build configuration and scripts.

**Examples:**

```
build: update webpack configuration
build: add production build script
build(docker): optimize image size
```

---

### `revert` - Revert Changes

Use `revert` when reverting a previous commit.

**Examples:**

```
revert: revert "feat: add new API endpoint"
revert: undo breaking changes from #123
```

---

## Breaking Changes

Add `!` after the type or `BREAKING CHANGE:` in the footer to indicate breaking changes:

```
feat!: remove deprecated API endpoints

BREAKING CHANGE: The old /api/v1 endpoints have been removed.
Use /api/v2 instead.
```

---

## Scopes

Add an optional scope to provide additional context:

```
feat(auth): add two-factor authentication
fix(ui): resolve navigation menu overflow
docs(api): update endpoint documentation
```
