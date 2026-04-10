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


def build_jd_quality_prompt(job_description):
    """Build the prompt for JD quality scoring."""
    return f"""You are evaluating a job description for signs of being a ghost job or low-quality posting.
Score each dimension where HIGHER scores indicate VAGUER descriptions (higher ghost job risk):

- problem_specificity (0-10): How generic are the responsibilities? 0=very specific outcomes, 10=generic buzzwords only
- team_context (0-8): How little team/org context is given? 0=clear team structure and stack, 8=no team context
- urgency_signal (0-7): How little urgency or timeline is conveyed? 0=clear start date/urgency, 7=no timeline signals

Job Description:
{job_description}

Return only a JSON object with exactly these fields:
{{
  "problem_specificity": <integer 0-10>,
  "team_context": <integer 0-8>,
  "urgency_signal": <integer 0-7>,
  "reasoning": "<brief one or two sentence explanation>"
}}"""


def collect_risk_inputs(post_interview=False):
    """Interactively collect risk signal inputs from the user."""
    print("\n--- Risk Assessment ---")

    days_str = input("How many days has this role been posted? ").strip()
    try:
        days_posted = int(days_str)
    except ValueError:
        days_posted = 0

    repost_raw = input("Have you seen this role before? (no/similar/exact): ").strip().lower()
    repost = repost_raw if repost_raw in ("similar", "exact") else "no"

    has_timeline = input("Does the posting include a hiring timeline? (y/n): ").strip().lower() == "y"

    market_research = False
    role_disappeared = False
    if post_interview:
        market_research = input("Did the interview feel like market research? (y/n): ").strip().lower() == "y"
        role_disappeared = input("Did the role disappear and reappear? (y/n): ").strip().lower() == "y"

    return {
        "days_posted": days_posted,
        "repost": repost,
        "has_timeline": has_timeline,
        "market_research": market_research,
        "role_disappeared": role_disappeared,
    }


def calculate_risk_score(risk_inputs, jd_quality):
    """Calculate the risk score from user inputs and LLM-scored JD quality."""
    # Category 1: Posting age (0-25)
    days = risk_inputs["days_posted"]
    if days <= 14:
        age_score = 0
    elif days <= 42:
        age_score = 10
    elif days <= 84:
        age_score = 20
    else:
        age_score = 25

    # Category 2: JD quality (0-25, sum of LLM sub-scores, capped at 25)
    jd_score = min(
        jd_quality["problem_specificity"] + jd_quality["team_context"] + jd_quality["urgency_signal"],
        25
    )

    # Category 3: Repost signal (0-25)
    repost_map = {"no": 0, "similar": 15, "exact": 25}
    repost_score = repost_map.get(risk_inputs["repost"], 0)

    # Category 4: Process signals (0-25)
    process_score = 0
    if not risk_inputs["has_timeline"]:
        process_score += 8
    if risk_inputs.get("market_research"):
        process_score += 10
    if risk_inputs.get("role_disappeared"):
        process_score += 7

    total = age_score + jd_score + repost_score + process_score

    return {
        "total": total,
        "posting_age": age_score,
        "jd_quality": jd_score,
        "repost_signal": repost_score,
        "process_signals": process_score,
    }


def risk_label(score):
    """Return a risk category label for the given score."""
    if score <= 25:
        return "Low risk — apply with full effort"
    elif score <= 50:
        return "Moderate risk — apply but don't over-invest"
    elif score <= 75:
        return "High risk — verify role is real before applying"
    else:
        return "Ghost job likely — proceed with eyes open"


def check(post_interview=False):
    """Read a job description from the clipboard and analyze fit."""
    config = load_config()

    job_description = pyperclip.paste().strip()
    if not job_description:
        print("Clipboard is empty. Copy a job description and try again.")
        return

    jobs_dir = Path(config["jobs_dir"]).expanduser()
    jobs_dir.mkdir(parents=True, exist_ok=True)

    model = config.get("model", DEFAULT_MODEL)

    risk_inputs = collect_risk_inputs(post_interview)

    print(f"\nAnalyzing with {model}...")

    # Call 1: JD quality scoring
    try:
        jd_response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": build_jd_quality_prompt(job_description)}],
            format="json",
            options={"temperature": 0.1},
        )
    except ollama.ResponseError as e:
        print(f"Ollama error: {e}")
        raise SystemExit(1)
    except Exception as e:
        print(f"Could not connect to Ollama. Is it running?\n{e}")
        raise SystemExit(1)

    try:
        jd_quality = json.loads(jd_response.message.content)
        _ = jd_quality["problem_specificity"]
        _ = jd_quality["team_context"]
        _ = jd_quality["urgency_signal"]
        _ = jd_quality["reasoning"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Unexpected response from model: {e}")
        print(jd_response.message.content)
        raise SystemExit(1)

    # Call 2: Fit assessment
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

    risk = calculate_risk_score(risk_inputs, jd_quality)
    label = risk_label(risk["total"])

    risk_breakdown = (
        f"Risk Breakdown:\n"
        f"  Posting age:     {risk['posting_age']}/25\n"
        f"  JD quality:      {risk['jd_quality']}/25\n"
        f"  Repost signal:   {risk['repost_signal']}/25\n"
        f"  Process signals: {risk['process_signals']}/25"
    )

    file_content = (
        f"Fit: {fit_score}/10\n"
        f"Risk: {risk['total']}/100 — {label}\n\n"
        f"{assessment}\n\n"
        f"{risk_breakdown}\n"
        f"JD Quality: \"{jd_quality['reasoning']}\"\n\n"
        f"---\n\n"
        f"{job_description}"
    )

    filepath = jobs_dir / filename
    with open(filepath, "w") as f:
        f.write(file_content)

    print(f"\nFit: {fit_score}/10")
    print(f"Risk: {risk['total']}/100 — {label}\n")
    print(assessment)
    print(f"\n{risk_breakdown}")
    print(f"JD Quality: \"{jd_quality['reasoning']}\"")
    print(f"\nSaved to {filepath}")


def main():
    parser = argparse.ArgumentParser(
        prog="fitcheck",
        description="Check your fit for a job posting."
    )
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Analyze a job description from your clipboard")
    check_parser.add_argument(
        "--post-interview",
        action="store_true",
        help="Enable post-interview risk flags (market research, role disappearance)"
    )

    config_parser = subparsers.add_parser("config", help="Manage your profile")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    config_subparsers.add_parser("edit", help="Edit your profile")

    args = parser.parse_args()

    if args.command == "check":
        check(post_interview=args.post_interview)
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
