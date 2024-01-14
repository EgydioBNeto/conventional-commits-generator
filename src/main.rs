use std::io::{self, Write};
use std::process::Command;

const RED: &str = "\x1b[91m";
const GREEN: &str = "\x1b[92m";
const YELLOW: &str = "\x1b[93m";
const RESET: &str = "\x1b[0m";

fn read_input(prompt: &str) -> String {
    print!("{}: ", prompt);
    io::stdout().flush().expect("Failed to flush stdout");
    let mut input: String = String::new();
    io::stdin().read_line(&mut input).expect("Failed to read input");
    input.trim().to_string()
}

fn choose_commit_type() -> String {
    let commit_types_explanations: [&str; 8] = [
        "feat - A new feature for the user or a particular enhancement",
        "fix - A bug fix for the user or a particular issue",
        "chore - Routine tasks, maintenance, or minor updates",
        "refactor - Code refactoring without changing its behavior",
        "style - Code style changes, formatting, or cosmetic improvements",
        "docs - Documentation-related changes",
        "test - Adding or modifying tests",
        "build - Changes that affect the build system or external dependencies",
    ];

    loop {
        println!("{}Choose the commit type:{}", YELLOW, RESET);
        for (i, commit_type_explanation) in commit_types_explanations.iter().enumerate() {
            println!("{}. {}", i + 1, commit_type_explanation);
        }

        let user_input: String = read_input(&format!("{}Choose the commit type or enter directly{}", YELLOW, RESET));

        match user_input.parse::<usize>() {
            Ok(index) if (1..=commit_types_explanations.len()).contains(&index) => {
                return commit_types_explanations[index - 1]
                    .split_whitespace()
                    .next()
                    .unwrap()
                    .to_lowercase();
            }
            _ => {
                if commit_types_explanations.iter().any(|ct: &&str| ct.split_whitespace().next().unwrap().eq_ignore_ascii_case(&user_input)) {
                    return user_input.to_lowercase();
                }
                println!("{}Invalid choice.{}", RED, RESET);
            }
        }
    }
}

fn generate_commit_message() -> Option<String> {
    let commit_type: String = choose_commit_type();
    let scope: String = read_input(&format!("{}Enter the scope (optional){}", YELLOW, RESET));

    loop {
        let message: String = read_input(&format!("{}Enter the commit message{}", YELLOW, RESET));

        if !message.is_empty() {
            let commit_message: String = match scope.is_empty() {
                true => format!("{}: {}", commit_type, message),
                false => format!("{}({}): {}", commit_type, scope, message),
            };

            println!("{}Commit message:\n{}{}\n{}", YELLOW, GREEN, commit_message, RESET);

            let confirm: String = read_input(&format!("{}Do you want to confirm this commit? (y/n){}", YELLOW, RESET)).to_lowercase();
            if confirm == "y" {
                return Some(commit_message);
            } else {
                println!("{}Commit canceled.{}", RED, RESET);
                break;
            }
        } else {
            println!("{}Commit message cannot be empty. Please enter a valid message.{}", RED, RESET);
        }
    }

    None
}

fn main() {
    if let Some(commit_message) = generate_commit_message() {
        if Command::new("git").arg("add").arg(".").status().is_err() {
            eprintln!("{}Failed to add changes to the staging area.{}", RED, RESET);
            return;
        }

        if Command::new("git").args(&["commit", "-m", &commit_message]).status().is_err() {
            eprintln!("{}Failed to commit changes.{}", RED, RESET);
            return;
        }

        println!("{}New commit successfully made, push to the repository{}", GREEN, RESET);
    }
}