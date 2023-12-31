# Conventional Commits Generator

<div align="center">
<img src="https://github.com/EgydioBNeto/conventional-commits-generator/assets/84047984/53f38934-16bb-40f6-aff7-a5800c4bd706" width="300px"/>
</div>

## Description

This script provides a simple yet powerful interactive interface for creating well-structured and standardized commit messages following the conventional commit format.

## Overview

```text
$ ccg

Choose the commit type:
1. feat - A new feature for the user or a particular enhancement
2. fix - A bug fix for the user or a particular issue
3. chore - Routine tasks, maintenance, or minor updates
...

Choose the commit type or enter directly (e.g., feat, fix, chore): feat

Enter the scope (optional, press Enter to skip): authentication

Enter the commit message: implement OAuth login

Commit message:
feat(authentication): implement OAuth login

Do you want to confirm this commit? (y/n): y

New commit successfully made, push to the repository
```

## Features

### Commands

- **ccg** : Generate a new commit.

## Requirements

- **Python3**

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
