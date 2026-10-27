# voice-agent-escalation-eval

An open evaluation harness and a small guard layer for **phone voice agents that must know when to stop and escalate**: when a caller describes an emergency, is in distress, asks for a human, or simply cannot be understood. It measures this separately for accented, code-mixed, older, fragmented and noisy speech, because those are the callers speech pipelines fail on most.

Everything here is synthetic text. It does not test any company's product, and it never places or receives a phone call.

The harness is general. A **domain** is a plug-in folder with its own scenario spec, baseline agent prompt and guard rules. Two domains are included:

| Domain | Setting | Why it matters |
|---|---|---|
| `gp_clinic` | AI receptionist for UK GP (family doctor) surgeries | Public reports in 2026 of AI receptionists failing callers with regional accents, speech affected by stroke, and callers who wanted a human. Sudden slurred speech is itself an NHS 999 sign. |
| `collections` | Indian loan EMI reminder and collection calls | RBI rules bar harassment and calls outside 8 AM to 7 PM. A collections bot must stop when the person is bereaved, distressed or mentions self-harm, and must not press someone who says they already paid. Callers speak Indian English, Hinglish and regional varieties, often on noisy lines. |

A separate real-audio slice (recorded accented speech through a phone-band ASR pipeline) is being built in [`audio_asr/`](audio_asr/README.md). See the section "Real-audio ASR slice" below.

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
- Each domain's scenarios are split 40/60 into dev and test, stratified by slice and group, **before** the guard was written. Guard rules were tuned on dev only. The GP guard was frozen in commit `ea2f56a` before any GP test run; the collections guard was frozen in its own commit before its test run (see `git log`).
- Headline numbers are on the **test** split.
- All LLM responses are cached in `cache/llm_cache.jsonl` keyed by a SHA-256 hash of the full request, so a rerun reproduces every number without network calls.
- `scripts/sanity_check.py` recomputes every headline proportion and interval with separate code and checks it against the summary.

## Results

RESULTS_PLACEHOLDER

## How to run

Windows or Linux, Python 3.12, CPU only.

```bash
pip install -r requirements.txt
# reproduce everything from the cache (no API key or network needed)
VAEVAL_OFFLINE=1 python scripts/run_eval.py --domain gp_clinic --split test --modes baseline guard
VAEVAL_OFFLINE=1 python scripts/run_eval.py --domain collections --split test --modes baseline guard
python scripts/sanity_check.py --domain gp_clinic --split test
python scripts/sanity_check.py --domain collections --split test
python scripts/error_analysis.py --domain gp_clinic --split test --mode guard
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
audio_asr/              real-audio ASR slice (built separately; see its README)
```

## Real-audio ASR slice (see audio_asr/README.md)

AUDIO_PLACEHOLDER

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
