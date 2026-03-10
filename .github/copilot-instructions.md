# Fitcheck - AI Coding Agent Instructions

## Project Overview
**Fitcheck** is a CLI-based job search configuration tool that helps users define and manage job search parameters (role, experience level, skills, location preferences). The project is in early development with foundational configuration setup logic in place.

## Architecture & Core Concepts

### Current Structure
- **`main.py`**: Entry point that handles configuration lifecycle
  - `build_config()`: Interactive CLI for collecting user job preferences
  - Configuration persisted to `~/.fitcheck/config.json`
  - Conditional logic: if config exists, loads it; otherwise triggers setup

### Key Workflow
1. User runs fitcheck → checks for existing `~/.fitcheck/config.json`
2. If missing: interactive `build_config()` prompts for:
   - Required: role, experience, skills, location, location_preference, relocation
   - Optional: refinement questions (in progress)
3. Configuration is user-specific, stored in home directory

## Development Patterns

### Configuration Management
- Use `pathlib.Path` for file operations (already established pattern in `main.py`)
- Store configuration in user's home directory as JSON files under `~/.fitcheck/`
- Example: `config_path = Path.home() / ".fitcheck" / "config.json"`

### CLI Interactions
- Use `input()` for user prompts with `.strip()` to handle whitespace
- Print section headers with formatting (see `build_config()` banner pattern)
- Provide user-friendly context before requesting input

## Expansion Patterns
When extending fitcheck, follow these patterns observed in `main.py`:
- Commands like `fitcheck config edit` suggest subcommand structure (implement as needed)
- Optional questions are deferred ("will help refine the result")
- Configuration structure should map to CLI prompts for consistency

## Notes for AI Agents
- **Early stage**: Expect incomplete features and TODO comments
- **Single file**: Keep monolithic structure until sufficient complexity warrants modularization
- **No dependencies**: Currently pure Python stdlib (pathlib, built-in input)
- **Configuration-driven**: User preferences are the core data model
