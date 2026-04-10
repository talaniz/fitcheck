![Tests](https://github.com/talaniz/fitcheck/actions/workflows/tests.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/talaniz/fitcheck/badge.svg?branch=main)](https://coveralls.io/github/talaniz/fitcheck?branch=main)

# fitcheck

A CLI tool that analyzes your fit against a job posting using a local LLM via Ollama.

## Prerequisites

- [Ollama](https://ollama.com) installed and running locally
- At least one model pulled, e.g.:

  ```
  ollama pull llama3.2
  ```

- Python 3.10 or later

## Installation

```bash
git clone https://github.com/yourusername/fitcheck.git
cd fitcheck
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## First run

Run `fitcheck` with no arguments to set up your profile:

```
fitcheck
```

You will be prompted for your target role, years of experience, top skills, location, work location preference, and where to save job files. A few optional fields (industries, must-haves, deal breakers) help refine the analysis but can be skipped by pressing Enter.

Configuration is written to `~/.fitcheck/config.json`.

## Commands

| Command | Description |
|---|---|
| `fitcheck` | Run initial setup if no config exists, otherwise print help |
| `fitcheck check` | Analyze the job description currently in your clipboard |
| `fitcheck config edit` | Re-run the setup wizard to update your profile |

## How `fitcheck check` works

1. Reads the job description from your system clipboard (copy it before running the command)
2. Sends your profile and the job description to the local LLM
3. Receives a fit score (1–10) and a short written assessment
4. Prints the result to the terminal
5. Saves a file to your configured jobs directory

## Saved file format

Each analysis is saved as a `.txt` file named after the company and role (e.g. `acme_senior_engineer.txt`) in the directory you specified during setup (default: `~/fitcheck/jobs`).

The file contains:

```
Fit: 7/10

<2-3 paragraph assessment>

---

<original job description>
```

## Configuration

The config file lives at `~/.fitcheck/config.json`. You can edit it directly or re-run `fitcheck config edit`.

To use a different Ollama model, add a `"model"` key to the config file:

```json
{
  "model": "mistral",
  ...
}
```

The default model is `llama3.2`.

## Example Output
```
$ fitcheck check

Analyzing with llama3.2...

Fit: 8/10

Strong match overall. Your 5 years of experience with Python and Django aligns 
well with their stack. Remote preference matches their flexible work policy. 
The role emphasizes PostgreSQL and Docker, both in your skill set.

Minor gaps: They mention Kubernetes experience as a plus, which isn't in your 
profile. The role leans heavily on fintech domain knowledge, which may require 
a learning curve.

Saved to ~/fitcheck/jobs/acme_corp_senior_engineer.txt
```

## Planned

- ATS keyword scan: compare the job description against your profile to surface missing keywords that applicant tracking systems commonly filter on.
