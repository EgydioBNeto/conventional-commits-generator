#!/usr/bin/env python3

import sys
import os
import subprocess

SCRIPT_NAME = "script.py"
CONFIG_FILES = [os.path.expanduser("~/.bashrc"), os.path.expanduser("~/.zshrc")]
INSTALL_DIR = os.path.expanduser("~/ccg")
SCRIPT_URL = "https://raw.githubusercontent.com/EgydioBNeto/conventional-commits-generator/main/script.py"
UNINSTALL_URL = "https://raw.githubusercontent.com/EgydioBNeto/conventional-commits-generator/main/uninstall.py"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def uninstall_ccg():

    print("Uninstalling existing 'conventional-commits-generator'...")

    try:
        subprocess.run(["curl", "-fsSL", UNINSTALL_URL, "-o", f"{INSTALL_DIR}/uninstall.py"], check=True)
    except subprocess.CalledProcessError:
        print(f"Cannot download uninstall script from '{UNINSTALL_URL}'.")
        print("Please uninstall manually.")
        return

    os.chmod(f"{INSTALL_DIR}/uninstall.py", 0o755)

    try:
        subprocess.run([f"{INSTALL_DIR}/uninstall.py"], check=True)
    except subprocess.CalledProcessError:
        print("Uninstall script failed.")
        print("Please uninstall manually.")
        return
    
def install_ccg():

    print("Installing 'C.C.G'...")
    os.makedirs(INSTALL_DIR, exist_ok=True)
    subprocess.run(["curl", "-fsSL", SCRIPT_URL, "-o", f"{INSTALL_DIR}/{SCRIPT_NAME}"], check=True)
    os.chmod(f"{INSTALL_DIR}/{SCRIPT_NAME}", 0o755)
    for config_file in CONFIG_FILES:
        with open(config_file, "a", encoding="utf-8") as alias_file:
            alias_file.write(f"""
# CCG aliases start
alias ccg='python3 {INSTALL_DIR}/{SCRIPT_NAME}'
# CCG aliases end
""")
    print(GREEN + "C.C.G installed successfully, please restart your terminal!" + RESET)
    
def main():

    if os.path.exists(INSTALL_DIR):
        uninstall_ccg()

    install_ccg()

if __name__ == "__main__":
    try:
        main()
    except Exception as exception_error:
        print(exception_error)
        sys.exit(1)
