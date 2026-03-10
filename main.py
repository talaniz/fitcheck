"""Main module for starting fitcheck."""

from pathlib import Path


def build_config():
    """Create the configuration file."""
    print("\n" + "="*60)
    print("FITCHECK CONFIGURATION")
    print("="*60)
    print("Don't worry if it's not perfect, you can always "
          "go back and change it using `fitcheck config edit`.")

    role = input("What role are you looking for?: ").strip()
    experience = input("How many years of experience?: ").strip()
    skills = input("What are your top five skills?: ").strip()
    location = input("Where are you based?: ").strip()
    location_preference = input("Work location preference (Remote / Hybrid / On-site / Flexible)?: ")
    relocation = input("Would you consider relocating? (yes/no): ")

    print("\n"*2)
    print("These next few questions are optional, but will help "
          "refine the result.")




if __name__ == "__main__":
    config_path = Path.home() / ".fitcheck" / "config.json"
    if config_path.exists():
        print("Got your config!")
    else:
        print("Let's get your config ready!")
        build_config()
