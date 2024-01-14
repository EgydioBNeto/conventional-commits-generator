use std::env;
use std::fs;
use std::io::{self, Write};
use std::process::{Command, exit};

const SCRIPT_NAME: &str = "script.py";
const CONFIG_FILES: [&str; 2] = [".bashrc", ".zshrc"];
const INSTALL_DIR: &str = "~/ccg";
const SCRIPT_URL: &str = "https://raw.githubusercontent.com/EgydioBNeto/conventional-commits-generator/main/script.py";
const UNINSTALL_URL: &str = "https://raw.githubusercontent.com/EgydioBNeto/conventional-commits-generator/main/uninstall.py";

const GREEN: &str = "\x1b[92m";
const RED: &str = "\x1b[91m";
const YELLOW: &str = "\x1b[93m";
const RESET: &str = "\x1b[0m";

fn uninstall_ccg() {
    println!("Uninstalling existing 'conventional-commits-generator'...");

    if let Err(_) = Command::new("curl")
        .args(&["-fsSL", UNINSTALL_URL, "-o", &format!("{}/uninstall.py", INSTALL_DIR)])
        .status()
    {
        eprintln!("Cannot download uninstall script from '{}'.", UNINSTALL_URL);
        println!("Please uninstall manually.");
        return;
    }

    if let Err(_) = Command::new("chmod")
        .args(&["+x", &format!("{}/uninstall.py", INSTALL_DIR)])
        .status()
    {
        eprintln!("Failed to set execute permission on uninstall script.");
        println!("Please uninstall manually.");
        return;
    }

    if let Err(_) = Command::new(&format!("{}/uninstall.py", INSTALL_DIR)).status() {
        eprintln!("Uninstall script failed.");
        println!("Please uninstall manually.");
        return;
    }
}

fn install_ccg() {
    println!("Installing 'C.C.G'...");

    if let Err(_) = fs::create_dir_all(&format!("{}/bin", env::var("HOME").unwrap())) {
        eprintln!("Failed to create installation directory '{}'.", INSTALL_DIR);
        exit(1);
    }

    if let Err(_) = Command::new("curl")
        .args(&["-fsSL", SCRIPT_URL, "-o", &format!("{}/bin/{}", env::var("HOME").unwrap(), SCRIPT_NAME)])
        .status()
    {
        eprintln!("Cannot download script from '{}'.", SCRIPT_URL);
        exit(1);
    }

    if let Err(_) = Command::new("chmod")
        .args(&["+x", &format!("{}/bin/{}", env::var("HOME").unwrap(), SCRIPT_NAME)])
        .status()
    {
        eprintln!("Failed to set execute permission on script.");
        exit(1);
    }

    for config_file in CONFIG_FILES.iter() {
        let alias_line = format!(
            "\n# CCG aliases start\nalias ccg='python3 {}/bin/{}'\n# CCG aliases end\n",
            env::var("HOME").unwrap(),
            SCRIPT_NAME
        );

        if let Ok(mut file) = fs::OpenOptions::new()
            .write(true)
            .append(true)
            .open(&format!("{}/{}", env::var("HOME").unwrap(), config_file))
        {
            if let Err(_) = file.write_all(alias_line.as_bytes()) {
                eprintln!("Failed to write alias to '{}'.", config_file);
                exit(1);
            }
        } else {
            eprintln!("Failed to open '{}'.", config_file);
            exit(1);
        }
    }

    println!("{}C.C.G installed successfully, please restart your terminal!{}", GREEN, RESET);
}

fn main() {
    if fs::metadata(&format!("{}/bin", env::var("HOME").unwrap())).is_ok() {
        uninstall_ccg();
    }

    install_ccg();
}
