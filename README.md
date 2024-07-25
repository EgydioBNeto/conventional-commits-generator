# Conventional Commits Generator

<div align="center">
<img src="https://github.com/EgydioBNeto/conventional-commits-generator/assets/84047984/53f38934-16bb-40f6-aff7-a5800c4bd706" width="300px"/>
</div>

## Description

This script provides a simple yet powerful interactive interface for creating well-structured and standardized commit messages following the conventional commit format.

## Overview

```text
$ ccg

1. feat - A new feature for the user or a particular enhancement
2. fix - A bug fix for the user or a particular issue
3. chore - Routine tasks, maintenance, or minor updates
...

Choose the commit type: feat

Enter the scope (optional): authentication

Is this a BREAKING CHANGE? (y/n): n

Enter the commit message: implement OAuth login

Commit message:
feat(authentication): implement OAuth login

Confirm this commit? (y/n): y

New commit successfully made.

Do you want to push these changes? (y/n): y

Changes pushed.

```

## Features

### Commands

- **ccg** : Generate a new commit.
- **ccg --push** : Just run git push.

## Requirements

- **Python3**
- **Git**

## Installation

```bash
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/EgydioBNeto/conventional-commits-generator/main/install.py)"
```

## Uninstallation

```bash
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/EgydioBNeto/conventional-commits-generator/main/uninstall.py)"
```

## Author

[EgydioBNeto](https://github.com/EgydioBNeto)

## License

This project is licensed under the [MIT License](https://github.com/EgydioBNeto/conventional-commits-generator/blob/main/LICENSE).
