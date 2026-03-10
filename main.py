"""Main module for starting fitcheck."""

import json
from pathlib import Path


CONFIG_PATH = Path.home() / ".fitcheck" / "config.json"


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

    print("\n"*2)
    print("These next few questions are optional, but will help "
          "refine the result.")
    print("If you don't want to answer, just hit enter and we'll skip it.\n\n")
    industries = [x.strip() for x in input("What industries are you interested in? (comma-separated): ").split(",") if x.strip()]
    must_haves = [x.strip() for x in input("What are your must-haves in a job? (comma-separated): ").split(",") if x.strip()]
    deal_breakers = [x.strip() for x in input("What are your deal breakers in a job? (comma-separated): ").split(",") if x.strip()]

    with open(CONFIG_PATH, "w") as f:
        json.dump({
            "role": role,
            "experience": experience,
            "skills": skills,
            "location": location,
            "location_preference": location_preference,
            "relocation": relocation,
            "industries": industries,
            "must_haves": must_haves,
            "deal_breakers": deal_breakers
        }, f, indent=2)

    print("Config file written to", CONFIG_PATH)


if __name__ == "__main__":
    if CONFIG_PATH.exists():
        print("Got your config!")
    else:
        print("Let's get your config ready!")
        build_config()
