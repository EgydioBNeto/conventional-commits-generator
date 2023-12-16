#!/usr/bin/env python3

import os
import shutil
import re
import sys

INSTALL_DIR = os.path.expanduser("~/ccg")
CONFIG_FILES = [os.path.expanduser("~/.bashrc"), os.path.expanduser("~/.zshrc")]
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def uninstall_ccg():
    
    try:
        if os.path.exists(INSTALL_DIR):
            shutil.rmtree(INSTALL_DIR)
    except Exception as e:
        print("Error removing directory %s: %s" % (INSTALL_DIR, e))
        sys.exit(1)

    for config_file in CONFIG_FILES:
        if not os.path.exists(config_file):
            continue

        with open(config_file, 'r', encoding='utf-8') as export_file:
            lines = export_file.readlines()

        with open(config_file, 'w', encoding='utf-8') as export_file:
            inside_aliases_section = False
            for line in lines:
                if re.search(r'# CCG aliases start', line):
                    inside_aliases_section = True
                    continue
                elif re.search(r'# CCG aliases end', line):
                    inside_aliases_section = False
                    continue

                if not inside_aliases_section:
                    export_file.write(line)

    print(GREEN + "Environment cleanup complete." + RESET)

def main():
    
    uninstall_ccg()
    
if __name__ == "__main__":
    try:
        main()
    except Exception as exception_error:
        print(exception_error)
        sys.exit(1)
