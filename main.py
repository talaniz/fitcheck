"""Main module for starting fitcheck."""

import json
import argparse
from pathlib import Path

import ollama
import pyperclip


CONFIG_PATH = Path.home() / ".fitcheck" / "config.json"
DEFAULT_MODEL = "llama3.2"


def build_config():
    """Create the configuration file."""
    print("\n" + "="*60)
    print("FITCHECK CONFIGURATION")
    print("="*60)
    print("Don't worry if it's not perfect, you can always "
          "go back and change it using `fitcheck config edit`.")

    role = input("What role are you looking for?: ").strip()
    experience = input("How many years of experience?: ").strip()
    skills = [x.strip() for x in input("What are your top five skills?: ").split(",") if x.strip()]
    location = input("Where are you based?: ").strip()
    location_preference = input("Work location preference (Remote / Hybrid / On-site / Flexible)?: ")
    relocation = input("Would you consider relocating? (yes/no): ")
    jobs_dir_input = input("Where should job files be saved? (default: ~/fitcheck/jobs): ").strip()
    jobs_dir = jobs_dir_input if jobs_dir_input else "~/fitcheck/jobs"

    print("\n"*2)
    print("These next few questions are optional, but will help "
          "refine the result.")
    print("If you don't want to answer, just hit enter and we'll skip it.\n\n")
    industries = [x.strip() for x in input("What industries are you interested in? (comma-separated): ").split(",") if x.strip()]
    must_haves = [x.strip() for x in input("What are your must-haves in a job? (comma-separated): ").split(",") if x.strip()]
    deal_breakers = [x.strip() for x in input("What are your deal breakers in a job? (comma-separated): ").split(",") if x.strip()]

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({
            "role": role,
            "experience": experience,
            "skills": skills,
            "location": location,
            "location_preference": location_preference,
            "relocation": relocation,
            "jobs_dir": jobs_dir,
            "industries": industries,
            "must_haves": must_haves,
            "deal_breakers": deal_breakers
        }, f, indent=2)

    print("Config file written to", CONFIG_PATH)


def load_config():
    """Load config, exiting with a helpful message if it doesn't exist."""
    if not CONFIG_PATH.exists():
        print("No config found. Run `fitcheck` to set up your profile.")
        raise SystemExit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def build_prompt(config, job_description):
    """Build the prompt for the LLM."""
    profile_lines = [
        f"Role seeking: {config['role']}",
        f"Experience: {config['experience']} years",
        f"Skills: {', '.join(config['skills'])}",
        f"Location: {config['location']}",
        f"Work preference: {config['location_preference']}",
        f"Open to relocation: {config['relocation']}",
    ]
    if config.get("industries"):
        profile_lines.append(f"Industries of interest: {', '.join(config['industries'])}")
    if config.get("must_haves"):
        profile_lines.append(f"Must-haves: {', '.join(config['must_haves'])}")
    if config.get("deal_breakers"):
        profile_lines.append(f"Deal breakers: {', '.join(config['deal_breakers'])}")

    profile = "\n".join(profile_lines)

    return f"""You are a job fit analyzer. Given a candidate profile and a job description, analyze the fit.

Candidate Profile:
{profile}

Job Description:
{job_description}

Return a JSON object with exactly these fields:
- "filename": a filename in the format "company_role.txt" (lowercase, underscores, no spaces, infer the company name from the job description)
- "fit_score": an integer from 1 to 10
- "assessment": a concise 2-3 paragraph assessment of the candidate's fit for this role, noting strengths and any gaps"""


def check():
    """Read a job description from the clipboard and analyze fit."""
    config = load_config()

    job_description = pyperclip.paste().strip()
    if not job_description:
        print("Clipboard is empty. Copy a job description and try again.")
        return

    jobs_dir = Path(config["jobs_dir"]).expanduser()
    jobs_dir.mkdir(parents=True, exist_ok=True)

    model = config.get("model", DEFAULT_MODEL)

    print(f"Analyzing with {model}...")

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": build_prompt(config, job_description)}],
            format="json",
        )
    except ollama.ResponseError as e:
        print(f"Ollama error: {e}")
        raise SystemExit(1)
    except Exception as e:
        print(f"Could not connect to Ollama. Is it running?\n{e}")
        raise SystemExit(1)

    try:
        result = json.loads(response.message.content)
        filename = result["filename"]
        fit_score = result["fit_score"]
        assessment = result["assessment"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Unexpected response from model: {e}")
        print(response.message.content)
        raise SystemExit(1)

    file_content = f"Fit: {fit_score}/10\n\n{assessment}\n\n---\n\n{job_description}"

    filepath = jobs_dir / filename
    with open(filepath, "w") as f:
        f.write(file_content)

    print(f"\nFit: {fit_score}/10\n")
    print(assessment)
    print(f"\nSaved to {filepath}")


def main():
    parser = argparse.ArgumentParser(
        prog="fitcheck",
        description="Check your fit for a job posting."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check", help="Analyze a job description from your clipboard")

    config_parser = subparsers.add_parser("config", help="Manage your profile")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    config_subparsers.add_parser("edit", help="Edit your profile")

    args = parser.parse_args()

    if args.command == "check":
        check()
    elif args.command == "config" and args.config_command == "edit":
        build_config()
    else:
        if not CONFIG_PATH.exists():
            print("Let's get your config ready!")
            build_config()
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
