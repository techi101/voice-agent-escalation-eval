# GP clinic phone line: escalation and handoff check

Nitesh Kumar Yadav, 28 Oct 2026. Repo: voice-agent-escalation-eval, domain `gp_clinic`.

## What I built

A test harness for AI phone receptionists at UK GP surgeries, a baseline receptionist agent I wrote myself (a Gemini Flash Lite prompt, not EMMA and not any vendor's product), and a small rule-based guard that reads each caller turn before the agent does. 200 synthetic call scenarios across 8 speech slices: standard UK English, regional dialect, non-native English, code-mixed Hindi/Urdu/Punjabi/Bengali with English, older rambling callers, fragmented speech of the kind a stroke can cause, injected ASR noise, and callers who keep asking for a person. The correct action for every scenario is written in code before any text is generated. The guard was tuned on the dev split only and frozen (commit ea2f56a) before the test split was run.

## Results

Test split. Cells are k/n, rate, [Wilson 95% interval].

**The test run is incomplete.** The free API quota for the agent model ran out partway through. The table covers the 50 of 119 test scenarios whose calls had all completed, in file order: mainly the standard, regional, non-native and code-mixed slices, plus one older caller. No follow-up completeness case is in this subset. The full run is one command once the quota resets (end of page).

| | Baseline agent | Agent + guard |
|---|---|---|
| Red-flag calls told to ring 999/111 | 17/17 = 100% [82%, 100%] | 17/17 = 100% [82%, 100%] |
| Calls that needed a human and got one | 8/16 = 50% [28%, 72%] | 15/16 = 94% [72%, 99%] |
| ...within the policy turn | 8/16 = 50% [28%, 72%] | 13/16 = 81% [57%, 93%] |
| Hard negatives wrongly told to ring 999/111 | 0/7 = 0% [0%, 35%] | 0/7 = 0% [0%, 35%] |
| Routine calls transferred without need | 1/17 = 6% [1%, 27%] | 1/17 = 6% [1%, 27%] |

Dev split (80 scenarios, all 8 slices; used for tuning, so optimistic for the guard):

| | Baseline agent | Agent + guard |
|---|---|---|
| Red-flag recall | 29/30 = 97% [83%, 99%] | 30/30 = 100% [89%, 100%] |
| Human handoff recall | 11/20 = 55% [34%, 74%] | 19/20 = 95% [76%, 99%] |
| False escalation on hard negatives | 0/15 = 0% [0%, 20%] | 0/15 = 0% [0%, 20%] |
| Follow-up completeness (asked which medicine or which test) | 9/10 = 90% [60%, 98%] | 10/10 = 100% [72%, 100%] |

The guard's rule checks take about 1 ms per caller turn (median 1.1 ms, 95th percentile about 4 ms).

## Three findings

1. **The baseline agent already escalated every red flag in these synthetic calls, so the guard added nothing there.** A plain prompt that says "call 999 in an emergency" caught face drooping, chest pain, sepsis signs and new speech difficulty even when they were buried mid-call or written in dialect or Hinglish. With 17 test cases the interval still allows real-world misses, and real ASR on real impaired speech was not tested.
2. **Where the baseline failed was getting stuck callers to a person.** It never transferred a caller whose name or date of birth kept being mangled ("Peter" written as "Pizza"); it kept asking again. The guard's counter (two failed captures, then hand off) fixed most of these. This matches the failure pattern in public reports about GP AI receptionists in 2026.
3. **The guard made one new mistake the baseline did not make.** In a code-mixed call where the caller was spelling her name, the Hindi words "bol" and "nahi" close together matched the "speech difficulty" rule and the guard told her to call 999. Keyword rules on code-mixed text need a precision check per language, not only recall.

## Limits, plainly

Synthetic text written by an LLM, not real calls or real accents. Caller turns are scripted and do not react. The baseline is my own prompt, so nothing here says how EMMA behaves. The red-flag list comes from public nhs.uk pages and is not clinically validated; a Clinical Safety Officer would need to own it. Samples per slice are small. The test run is partial as stated above.

## Why this topic

Public reporting in 2026: at Gordon House surgery (Rory Cellan-Jones, Substack, 20 May 2026) a patient's name was logged as "Pizza", a patient was not asked which medicine, and patients shouted to reach a person. Healthwatch Rotherham (reported by BBC and others, 19 to 25 Aug 2026) said the AI struggled with regional accents and speech impediments. A stroke survivor at an Armthorpe practice could not get past the AI after five tries (BBC, about 27 Aug 2026). The NHS lists slurred or sudden difficult speech as a stroke and sepsis warning sign. QuantumLoopAI's own blog (22 Apr 2026) asks providers whether they measure performance across accent groups. This harness is one way to measure that for escalation and handoff.

To finish the test run after the quota resets: `python scripts/run_eval.py --domain gp_clinic --split test`.
