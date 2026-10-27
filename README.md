# voice-agent-escalation-eval

An open evaluation harness and a small guard layer for **phone voice agents that must know when to stop and escalate**: when a caller describes an emergency, is in distress, asks for a human, or simply cannot be understood. It measures this separately for accented, code-mixed, older, fragmented and noisy speech, because those are the callers speech pipelines fail on most.

Everything here is synthetic text. It does not test any company's product, and it never places or receives a phone call.

The harness is general. A **domain** is a plug-in folder with its own scenario spec, baseline agent prompt and guard rules. Two domains are included:

| Domain | Setting | Why it matters |
|---|---|---|
| `gp_clinic` | AI receptionist for UK GP (family doctor) surgeries | Public reports in 2026 of AI receptionists failing callers with regional accents, speech affected by stroke, and callers who wanted a human. Sudden slurred speech is itself an NHS 999 sign. |
| `collections` | Indian loan EMI reminder and collection calls | RBI rules bar harassment and calls outside 8 AM to 7 PM. A collections bot must stop when the person is bereaved, distressed or mentions self-harm, and must not press someone who says they already paid. Callers speak Indian English, Hinglish and regional varieties, often on noisy lines. |

All results here are on text transcripts. A real-audio check (recorded accented speech through phone-band ASR) is not part of this repo yet.

---

## The problem, in one paragraph

A voice agent hears the caller through speech recognition (ASR). ASR is least accurate for regional accents, non-native speakers, code-mixed speech and impaired speech, and the agent only ever sees the ASR's text. If the agent's escalation logic lives only in an LLM prompt, there is no measurement of how often it escalates when it should, how often it escalates when it should not, or how many turns a struggling caller must go through to reach a person. This repo measures exactly that, per speech slice, with confidence intervals, and tests whether a small deterministic guard in front of the agent helps.

## What is in the box

1. **Scenario specs written in code** (`domains/<name>/spec.py`). Every test case has its slice, its content plan, the turn where the key signal appears, the expected action and the follow-up fields staff will need. These are the ground-truth labels. No LLM decides a label.
2. **LLM-written caller turns** from those specs, checked by a second LLM prompt with literal yes/no questions and plain code accept rules, then spot-checked by hand. Deterministic ASR noise is added for the noise slices.
3. **A baseline agent per domain**: a plausible LLM agent prompt written for this project. It is a stand-in, not any vendor's agent.
4. **A guard layer** (`vaeval/guard.py` plus `domains/<name>/guard_config.py`) that reads each caller turn before the agent: fuzzy word-pair rules for must-escalate signals (with romanised Hindi, Urdu, Punjabi and Bengali terms), human-request detection that never blocks a request, a failed-capture counter (hand off after 2), follow-up completeness notes, and for collections a pre-call check of the 8 AM to 7 PM rule.
5. **Metrics by slice with Wilson 95% intervals**, before and after the guard, plus an independent recomputation script, an error-analysis script and unit tests.

## Method and honesty rules

- Labels come from the spec in code. The LLM only writes the words.
- Each domain's scenarios are split 40/60 into dev and test, stratified by slice and group, **before** the guard was written. Guard rules were tuned on dev only. The GP guard was frozen in commit `ea2f56a` before any GP test run; the collections guard was written from the RBI rules and unit tests and frozen in commit 6b049b2 before any collections call was run; it was never tuned on data.
- Headline numbers are on the **test** split.
- All LLM responses are cached in `cache/llm_cache.jsonl` keyed by a SHA-256 hash of the full request, so a rerun reproduces every number without network calls.
- `scripts/sanity_check.py` recomputes every headline proportion and interval with separate code and checks it against the summary.

## Results

Full tables by slice: `results/<domain>/test/results.md`. Remaining errors with full calls: `results/<domain>/test/errors_guard.md`. Cells are k/n = rate [Wilson 95% interval].

### Domain 1: gp_clinic (test split, PARTIAL: 50 of 119 scenarios)

The free daily quota for the agent model ran out during the test run. These 50 are the test scenarios whose calls had all completed, in file order (mostly standard, regional, non-native and code-mixed slices; no follow-up case). `python scripts/run_eval.py --domain gp_clinic --split test` completes the run when the quota resets.

| Metric | Baseline agent | Agent + guard |
|---|---|---|
| Red-flag escalation recall | 17/17 = 100% [82%, 100%] | 17/17 = 100% [82%, 100%] |
| Human handoff recall | 8/16 = 50% [28%, 72%] | 15/16 = 94% [72%, 99%] |
| Handoff within policy turn | 8/16 = 50% [28%, 72%] | 13/16 = 81% [57%, 93%] |
| False escalation (hard negatives) | 0/7 = 0% [0%, 35%] | 0/7 = 0% [0%, 35%] |
| Unneeded transfer (routine + hard neg) | 1/17 = 6% [1%, 27%] | 1/17 = 6% [1%, 27%] |

Dev split (80 scenarios, all slices, used for tuning): red-flag recall 29/30 vs 30/30; handoff 11/20 vs 19/20; follow-up completeness 9/10 vs 10/10; false escalation 0/15 for both.

What it shows: the baseline prompt already escalated every red flag in this synthetic set, so the guard added nothing there. The gain is in getting stuck callers (mangled names or dates of birth) to a human. The guard also made one new error: Hindi words in a name-spelling call matched its "speech difficulty" rule and it advised 999. Details: [REPORT_gp_clinic.md](REPORT_gp_clinic.md).

### Domain 2: collections (test split, 79 scenarios)

| Metric | Baseline agent | Agent + guard |
|---|---|---|
| Must-escalate recall (self-harm, distress, bereavement, harassment) | 14/16 = 88% [64%, 97%] | 16/16 = 100% [81%, 100%] |
| Compliance stop (stop request, wrong number, outside 8 AM to 7 PM) | 4/10 = 40% [17%, 69%] | 10/10 = 100% [72%, 100%] |
| Human handoff recall | 21/29 = 72% [54%, 85%] | 28/29 = 97% [83%, 99%] |
| Handoff within policy turn | 21/29 = 72% [54%, 85%] | 26/29 = 90% [74%, 96%] |
| False stop/escalation (hard negatives) | 0/6 = 0% [0%, 39%] | 0/6 = 0% [0%, 39%] |
| Unneeded transfer (routine + hard neg) | 0/24 = 0% [0%, 14%] | 1/24 = 4% [1%, 20%] |
| Follow-up completeness (amount and date) | 7/12 = 58% [32%, 81%] | 11/12 = 92% [65%, 99%] |

What it shows: the baseline was told the 8 AM to 7 PM rule and the local time, and still kept collecting in all 4 out-of-hours test calls; a clock check in code fixed them. No dispute cases survived data checking, so dispute handling is not measured. The collections guard was frozen before any collections run and never tuned on data. Details: [REPORT_collections.md](REPORT_collections.md).

Guard rule latency: about 1 ms per caller turn in both domains.

### Why these two domains

- **GP clinics (UK).** In 2026, public reports described AI phone receptionists at GP surgeries failing callers: at Gordon House surgery a patient's name was logged as "Pizza", a patient was not asked which medicine, and patients shouted to reach a person (Rory Cellan-Jones, Substack, 20 May 2026); Healthwatch Rotherham reported trouble with regional accents and speech impediments (BBC and others, 19 to 25 Aug 2026); a stroke survivor at a Doncaster-area practice could not get past the AI after five tries (BBC, about 27 Aug 2026; NR Times 27 Aug 2026). The NHS lists slurred or sudden difficult speech as a stroke and sepsis warning sign (nhs.uk stroke and sepsis pages). No public report found says any AI receptionist missed a red flag; this harness only measures the risk.
- **Collections (India).** RBI/2022-23/108 (12 Aug 2022) bars intimidation, harassment, repeated calls and recovery calls before 8 AM or after 7 PM; RBI/2007-08/296 (24 Apr 2008) says recovery should wait while a borrower's grievance is open; an RBI draft of 12 Feb 2026 adds avoiding calls during bereavement or calamity. Voice AI is increasingly used for these calls, and callers speak Indian English, Hinglish and regional varieties, often on noisy lines.


## How to run

Windows or Linux, Python 3.12, CPU only.

```bash
pip install -r requirements.txt
# reproduce everything from the cache (no API key or network needed)
python scripts/run_eval.py --domain gp_clinic --split test --modes baseline guard --cached-only
VAEVAL_OFFLINE=1 python scripts/run_eval.py --domain collections --split test --modes baseline guard
python scripts/sanity_check.py --domain gp_clinic --split test
python scripts/sanity_check.py --domain collections --split test
python scripts/error_analysis.py --domain gp_clinic --split test --mode guard
# the GP test split is partial (quota); reproduce the published table with --cached-only
python -m pytest -q
```

On Windows PowerShell set the variables with `$env:VAEVAL_OFFLINE="1"; $env:PYTHONIOENCODING="utf-8"` first.

To regenerate from scratch you need a `GEMINI_API_KEY` environment variable (free tier is enough, but daily per-model limits apply, so a full rebuild can take more than one day):

```bash
python scripts/build_dataset.py --domain collections
python scripts/run_eval.py --domain collections --split dev
python scripts/run_eval.py --domain collections --split test
```

### Adding a domain

Copy `domains/collections/` and change: `spec.py` (slices, kinds, expected actions, hard negatives), `writer.py` (writer and checker prompts, accept rules), `agent_prompt.py`, `guard_config.py`, `noise.py`, `followup_patterns.py`, and the `METRICS` list in `__init__.py`. Then add the name to `vaeval/domain.py`.

## Repository layout

```
vaeval/                 shared harness: llm cache, scenario, generate, asr_noise, matcher, guard, runner, metrics
domains/gp_clinic/      domain 1: spec, writer, agent prompt, guard config, noise, follow-up patterns
domains/collections/    domain 2: same files
scripts/                build_dataset, run_eval, sanity_check, error_analysis, voice_name_slice (TTS pilot)
tests/                  pytest unit tests (guards, metrics, Wilson intervals)
data/<domain>/          scenarios.jsonl (labels), transcripts.jsonl, validation_log.csv
results/<domain>/       dev/ and test/ results, spot_check.md
cache/                  every LLM response (no secrets)
```

A small earlier pilot is in `scripts/voice_name_slice.py` and `results/voice_names/`: 20 synthetic names spoken by two US-English Windows TTS voices over a simulated phone line and speakerphone, transcribed with faster-whisper small. Raw full-name accuracy was 9/20 (phone) and 0/20 (speakerphone). Giving Whisper the practice's name list as a prompt and fuzzy-matching to the list raised correct names to 10/20 and 5/20, but matched the caller to a **different** registered patient in 9/20 and 12/20 clips, because the list held similar-sounding names. A wrong confident match is worse than no match, so name-list biasing needs a second key such as date of birth. TTS voices are not real accents.

## Limitations

- **Synthetic text, not real calls.** Caller turns were written by an LLM following a spec. LLM-written dialect, code-mixing or "fragmented speech" is not the same as real accented or impaired speech, and nothing here measures real ASR accuracy for real speakers.
- **Scripted callers.** Caller turns do not react to what the agent says. Real conversations branch.
- **Stand-in agents.** The baseline agents are prompts written for this project. Results say nothing about EMMA, QuantumLoopAI, Bolna, Gnani, Skit.ai, Exotel or any other product.
- **No clinical or legal claim.** The GP red-flag list comes from public nhs.uk pages and is not clinically validated or complete; a clinician (for example a practice's Clinical Safety Officer) would need to own it. The collections rules come from public RBI circulars (one of them a draft) and design choices stated in `domains/collections/spec.py`; this is not legal or compliance advice.
- **Same author for noise and guard.** The ASR-noise injector and the guards were written in the same project, so the noise slices may be easier for the guards than real ASR errors would be.
- **Small samples.** Per-slice test cells hold roughly 5 to 15 cases. The Wilson intervals are wide; read slice-level differences as signals to investigate, not as findings.
- **Keyword guards have blind spots.** They miss paraphrases outside their word lists (see each domain's `errors_guard.md`), and they can fire on idioms. The false-escalation rate on hard negatives is reported for that reason.

## AI-use disclosure

This project was built with Claude Code (an AI coding assistant) directing most of the code, prompts and documents, under the author's direction and review. Specifically: Claude Code wrote the harness, the scenario specs, the prompts, the guard word lists, the tests and the first drafts of these documents; Google Gemini models (Flash and Flash Lite, free tier) and Google's open Gemma model wrote the synthetic caller turns and played the baseline agents. The author chose the problem, set the honesty rules (labels from code, dev/test split, no claims about real products), reviewed the outputs and the spot checks, and is responsible for the content.
