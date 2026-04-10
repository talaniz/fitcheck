# Understanding the fitcheck Risk Score

## What is the Risk Score?

The fitcheck risk score estimates the likelihood that a job posting is a ghost job, a pipeline-building exercise, or an otherwise low-quality opportunity — before you invest significant time applying.

It does not measure whether you are qualified for the role. That is what the fit score is for. The risk score measures whether the role is worth your effort in the first place.

## Why This Matters

Not every job posting represents a real, open opportunity. Companies post roles for a variety of reasons that have nothing to do with hiring someone from the outside:

- **Internal process compliance** — a role has already been promised to an internal candidate, but policy requires an external posting
- **Pipeline building** — the company wants to know who is available in the market for a future hire, with no current opening
- **Administrative neglect** — a role was filled weeks or months ago but nobody took the listing down

None of this is visible from the outside. The risk score gives you a structured way to evaluate the signals before you commit.

## How the Score Works

The risk score is calculated across four categories, each worth up to 25 points. A higher score means higher risk.

---

### Category 1: Posting Age (0–25 points)

The longer a role has been live without movement, the more likely something is off.

| Days Posted | Points |
|-------------|--------|
| 0–14 days | 0 |
| 15–42 days | 10 |
| 43–84 days | 20 |
| 85+ days | 25 |

Real urgent hires move quickly. If a listing has been sitting untouched for six weeks or more, it is worth checking whether the company has actually brought anyone new into that team recently before investing serious time.

---

### Category 2: JD Quality (0–25 points)

fitcheck uses an LLM to evaluate the quality of the job description itself. A well-written JD — one with a specific problem to solve, clear team context, and some indication of urgency — is a strong signal that a real hiring manager wrote it because they actually need someone.

A vague JD full of generic duties and no specific context is often a sign the posting was written to satisfy a process rather than find a specific person.

The LLM evaluates three dimensions:

| Dimension | Max Points | What It Measures |
|-----------|------------|------------------|
| Problem specificity | 10 | Does the JD describe a specific problem to solve, or just list duties? |
| Team context | 8 | Is there a clear team, reporting structure, or organizational context? |
| Urgency signal | 7 | Is there any indication of timeline, start date, or hiring urgency? |

A brief explanation of the scoring is included in your fitcheck output so you understand why the JD received the score it did.

---

### Category 3: Repost Signal (0–25 points)

A role that has appeared before — especially with slightly different wording — is a warning sign. It usually means the role either lost budget and came back, the first round of hiring failed, or the role was never quite real to begin with.

| Signal | Points |
|--------|--------|
| First time seeing this role | 0 |
| Similar role appeared before with different wording | 15 |
| Exact same role reposted | 25 |

---

### Category 4: Process Signals (0–25 points)

These signals come from your direct experience with the posting or the interview process.

| Signal | Points |
|--------|--------|
| No hiring timeline mentioned in the JD | 8 |
| Interview felt like market research rather than evaluation | 10 |
| Role disappeared and reappeared | 7 |

The interview-feel and reappearance signals are only available via the `--post-interview` flag, since they require direct experience with the process.

---

## Interpreting Your Score

| Score | Label | What It Means |
|-------|-------|---------------|
| 0–25 | Low risk | Apply with full effort |
| 26–50 | Moderate risk | Apply, but don't over-invest |
| 51–75 | High risk | Do a LinkedIn verification pass before applying |
| 76–100 | Ghost job likely | Proceed with eyes open |

## A Note on Judgment

The risk score is a tool, not a verdict. A high score does not mean you should not apply. It means you should be more deliberate about how much time and energy you invest before you have stronger signal that the opportunity is real.

Targeted applications to companies that are actively hiring — recent activity on LinkedIn, teams that are growing, roles posted in the last two to three weeks — will always outperform volume applications to listings that have been sitting since January.

The risk score helps you allocate your effort where it is most likely to pay off.

## Usage

Run the risk score alongside your fit assessment:

```bash
fitcheck check <job_description>
```

fitcheck will prompt you for the inputs it needs to calculate your risk score and include it in the final report.

For post-interview risk assessment:

```bash
fitcheck check <job_description> --post-interview
```
