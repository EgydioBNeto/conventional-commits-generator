"""Core functionality for the Conventional Commits Generator."""

import shutil
import subprocess
import sys
from typing import Dict, List, Optional

# Adicionando a importação da prompt_toolkit com tratamento adequado
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style

    # Inicializar históricos apenas se a biblioteca estiver disponível
    type_history = InMemoryHistory()
    scope_history = InMemoryHistory()
    message_history = InMemoryHistory()

    # Estilo para prompt_toolkit
    prompt_style = Style.from_dict(
        {
            "prompt": "#00AFFF bold",
            "command": "#00FF00 bold",
            "option": "#FF00FF",
        }
    )

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    # Definir variáveis dummy para evitar erros de referência
    type_history = None
    scope_history = None
    message_history = None
    prompt_style = None

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

# Símbolos para melhorar a aparência
CHECK = "✓"
CROSS = "✗"
ARROW = "→"
STAR = "★"
DIAMOND = "♦"
HEART = "♥"
WARNING = "⚠"
INFO = "ℹ"
BULLET = "•"

# Obter tamanho do terminal
try:
    TERM_WIDTH, TERM_HEIGHT = shutil.get_terminal_size()
except Exception:
    TERM_WIDTH, TERM_HEIGHT = 80, 24

# Commit types com descrições e cores
COMMIT_TYPES: List[Dict[str, str]] = [
    {
        "type": "feat",
        "description": "A new feature for the user or a particular enhancement",
        "color": GREEN,
        "symbol": STAR,
    },
    {
        "type": "fix",
        "description": "A bug fix for the user or a particular issue",
        "color": RED,
        "symbol": HEART,
    },
    {
        "type": "chore",
        "description": "Routine tasks, maintenance, or minor updates",
        "color": BLUE,
        "symbol": BULLET,
    },
    {
        "type": "refactor",
        "description": "Code refactoring without changing its behavior",
        "color": MAGENTA,
        "symbol": DIAMOND,
    },
    {
        "type": "style",
        "description": "Code style changes, formatting, or cosmetic improvements",
        "color": CYAN,
        "symbol": BULLET,
    },
    {
        "type": "docs",
        "description": "Documentation-related changes",
        "color": WHITE,
        "symbol": INFO,
    },
    {
        "type": "test",
        "description": "Adding or modifying tests",
        "color": YELLOW,
        "symbol": CHECK,
    },
    {
        "type": "build",
        "description": "Changes that affect the build system or external dependencies",
        "color": YELLOW,
        "symbol": BULLET,
    },
    {
        "type": "revert",
        "description": "Reverts a previous commit",
        "color": RED,
        "symbol": ARROW,
    },
    {
        "type": "ci",
        "description": "Changes to CI configuration files and scripts",
        "color": BLUE,
        "symbol": BULLET,
    },
    {
        "type": "perf",
        "description": "A code change that improves performance",
        "color": GREEN,
        "symbol": ARROW,
    },
]


def print_header(text: str) -> None:
    """Print a stylized header."""
    padding = (TERM_WIDTH - len(text) - 4) // 2
    print()
    print(f"{CYAN}{BOLD}{'═' * padding} {text} {'═' * padding}{RESET}")
    print()


def print_section(text: str) -> None:
    """Print a section divider."""
    print()
    print(f"{BLUE}{BOLD}┌{'─' * (len(text) + 2)}┐{RESET}")
    print(f"{BLUE}{BOLD}│ {text} │{RESET}")
    print(f"{BLUE}{BOLD}└{'─' * (len(text) + 2)}┘{RESET}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{GREEN}{BOLD}{CHECK} {message}{RESET}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{RED}{BOLD}{CROSS} {message}{RESET}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{CYAN}{INFO} {message}{RESET}")


def print_process(message: str) -> None:
    """Print a process message."""
    print(f"{YELLOW}{ARROW} {message}{RESET}")


def read_input(prompt_text: str) -> str:
    """Read user input with a given prompt, supporting arrow keys and history."""
    if PROMPT_TOOLKIT_AVAILABLE:
        try:
            # Escolha o histórico apropriado com base no texto do prompt
            history = None
            if "commit type" in prompt_text.lower():
                history = type_history
            elif "scope" in prompt_text.lower():
                history = scope_history
            elif "commit message" in prompt_text.lower():
                history = message_history

            # Remover códigos ANSI da string do prompt para evitar problemas
            clean_prompt = prompt_text
            for code in [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD, UNDERLINE, RESET]:
                clean_prompt = clean_prompt.replace(code, "")

            # Use prompt_toolkit com configuração básica, sem HTML ou estilo personalizado
            result = prompt(
                f"{clean_prompt}: ",
                history=history
            ).strip()

            return result
        except Exception:
            # Em caso de erro, volta para o input padrão
            return input(f"{prompt_text}: ").strip()
    else:
        # Fallback para a função input() padrão
        return input(f"{prompt_text}: ").strip()

def display_commit_types() -> None:
    """Display available commit types with explanations."""
    print_header("Commit Types")

    # Calcula o número máximo de dígitos para o índice
    max_idx_len = len(str(len(COMMIT_TYPES)))

    # Calcula o comprimento máximo dos tipos para alinhamento
    max_type_len = max(len(commit_data["type"]) for commit_data in COMMIT_TYPES)

    # Imprime os tipos de commit em um formato agradável
    for i, commit_data in enumerate(COMMIT_TYPES, start=1):
        color = commit_data.get("color", WHITE)
        symbol = commit_data.get("symbol", BULLET)

        idx = f"{i}.".ljust(max_idx_len + 1)
        commit_type = commit_data["type"].ljust(max_type_len)

        print(
            f"{idx} {color}{BOLD}{symbol} {commit_type}{RESET} - {commit_data['description']}"
        )


def choose_commit_type() -> str:
    """Prompt the user to choose a commit type."""
    display_commit_types()
    print()

    while True:
        try:
            user_input = read_input(f"{YELLOW}Choose the commit type{RESET}")

            if user_input.isdigit() and 1 <= int(user_input) <= len(COMMIT_TYPES):
                commit_type = COMMIT_TYPES[int(user_input) - 1]["type"]
                print_success(f"Selected type: {BOLD}{commit_type}{RESET}")
                return commit_type

            # Check if the input matches a commit type directly
            for commit_data in COMMIT_TYPES:
                if user_input.lower() == commit_data["type"].lower():
                    print_success(f"Selected type: {BOLD}{commit_data['type']}{RESET}")
                    return commit_data["type"]

            print_error("Invalid choice. Please select a valid option.")
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            sys.exit(0)


def get_scope() -> Optional[str]:
    """Get the commit scope from user input."""
    print_section("Scope")
    print_info("The scope provides context for the commit (e.g., module or file name)")
    scope = read_input(f"{YELLOW}Enter the scope (optional){RESET}")

    if scope:
        print_success(f"Scope set to: {BOLD}{scope}{RESET}")
    else:
        print_info("No scope provided")

    return scope if scope else None


def is_breaking_change() -> bool:
    """Check if the commit is a breaking change."""
    print_section("Breaking Change")
    print_info("A breaking change means this commit includes incompatible API changes")

    while True:
        breaking = read_input(
            f"{YELLOW}Is this a BREAKING CHANGE? (y/n){RESET}"
        ).lower()
        if breaking in ("y", "n"):
            if breaking == "y":
                print_success(f"Marked as {BOLD}BREAKING CHANGE{RESET}")
            else:
                print_info("Not a breaking change")
            return breaking == "y"
        print_error("Invalid choice. Please enter 'y' or 'n'.")


def get_commit_message() -> str:
    """Get the commit message from user input."""
    print_section("Commit Message")
    print_info("Provide a clear, concise description of the change")

    while True:
        message = read_input(f"{YELLOW}Enter the commit message{RESET}")
        if message.strip():
            print_success(f"Message: {BOLD}{message}{RESET}")
            return message
        print_error("Commit message cannot be empty.")


def generate_commit_message() -> Optional[str]:
    """Generate a conventional commit message based on user input."""
    try:
        print_header("Conventional Commit Generator")

        # Get commit components
        commit_type = choose_commit_type()
        scope = get_scope()
        breaking_change = is_breaking_change()
        message = get_commit_message()

        # Construct the commit message
        breaking_indicator = "!" if breaking_change else ""
        scope_part = f"({scope})" if scope else ""
        header = f"{commit_type}{breaking_indicator}{scope_part}: "
        commit_message = f"{header}{message}"

        # Display and confirm
        print_section("Review")
        print(f"{CYAN}Your commit message:{RESET}")
        print()
        print(f"{GREEN}{BOLD}{commit_message}{RESET}")
        print()

        while True:
            confirm = read_input(f"{YELLOW}Confirm this commit? (y/n){RESET}").lower()
            if confirm in ("y", "n"):
                if confirm == "y":
                    print_success("Commit message confirmed!")
                    return commit_message
                print("\nExiting. Goodbye!")
                sys.exit(0)
            print_error("Invalid choice. Please enter 'y' or 'n'.")

    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)

    return None


def git_add() -> bool:
    """Run 'git add' to stage changes."""
    try:
        print_process("Staging changes with git...")
        subprocess.run(["git", "add", "."], capture_output=True, check=True)
        print_success("Changes staged successfully")
        return True
    except subprocess.CalledProcessError as error:
        print_error("Error during 'git add':")
        print(f"{RED}{error.stderr.decode()}{RESET}")
        return False
    except FileNotFoundError:
        print_error("Git is not installed. Please install Git and try again.")
        return False


def git_commit(commit_message: str) -> bool:
    """Run 'git commit' with the provided message."""
    try:
        print_process("Committing changes...")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print_success("New commit successfully created!")
        return True
    except subprocess.CalledProcessError:
        print_error("Error during 'git commit'")
        return False


def confirm_push() -> bool:
    """Ask user to confirm push."""
    print_section("Push Changes")
    print_info("You can push your changes to the remote repository")

    confirm = read_input(
        f"{YELLOW}Do you want to push these changes? (y/n){RESET}"
    ).lower()

    if confirm == "y":
        print_info("Preparing to push changes...")
    else:
        print_info("Not pushing changes")

    return confirm == "y"


def git_push() -> bool:
    """Run 'git push' to push changes."""
    try:
        print_process("Pushing changes to remote repository...")
        subprocess.run(["git", "push"], check=True)
        print_success("Changes pushed successfully!")
        return True
    except subprocess.CalledProcessError:
        print_error("Error during 'git push'")
        return False


def check_and_install_pre_commit() -> bool:
    """Check for pre-commit config and install hooks if needed."""
    try:
        # Check if .pre-commit-config.yaml exists
        with open(".pre-commit-config.yaml", "r"):
            pass

        # Check if pre-commit is installed
        try:
            subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)

            # Install pre-commit hooks
            print_process("Setting up pre-commit hooks...")
            subprocess.run(["pre-commit", "install"], check=True, capture_output=True)
            print_success("Pre-commit hooks installed successfully")

            # Run pre-commit against staged files
            print_process("Running pre-commit checks on staged files...")

            # Get the list of staged files using a separate subprocess call
            staged_files_process = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                check=False,
                capture_output=True,
                text=True,
            )

            if staged_files_process.returncode == 0:
                # Split the output into a list of files
                staged_files = staged_files_process.stdout.strip().split("\n")

                # Only run pre-commit if there are staged files
                if staged_files and staged_files[0]:
                    result = subprocess.run(
                        ["pre-commit", "run", "--files"] + staged_files,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode != 0:
                        print_error(
                            "Some pre-commit checks failed. Exiting the script."
                        )
                        # Display the output
                        print(result.stdout)
                        print(result.stderr)
                        # Return False when pre-commit fails
                        return False

            print_success("All pre-commit checks passed successfully")
            return True

        except (FileNotFoundError, subprocess.CalledProcessError):
            print_info("pre-commit is configured but not installed.")
            print_info("Run 'pip install pre-commit' to install it.")
            print_info(
                "After installing, run 'pre-commit install' to set up the hooks."
            )
            return False

    except FileNotFoundError:
        # No pre-commit config found, that's okay
        return True
