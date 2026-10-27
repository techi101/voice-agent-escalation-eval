# Loan EMI collection calls (India): escalation and compliance check

Nitesh Kumar Yadav, 28 Oct 2026. Repo: voice-agent-escalation-eval, domain `collections`.

## What I built

The same harness as the GP domain, pointed at automated EMI reminder and collection calls for a made-up Indian NBFC. The baseline agent is my own Gemini 3.1 Flash Lite prompt that already states the main RBI rules in plain words (no harassment, calls only 8 AM to 7 PM, log disputes, escalate distress). It is not any vendor's agent. The guard is a small rule layer in front of it: a clock check for the 8 AM to 7 PM rule, word-pair rules (English and Hinglish) for self-harm, bereavement, harassment complaints and severe distress, patterns for "stop calling", "wrong number", "already paid" and human requests, a failed-capture counter, and a note asking the agent for a missing promise amount or date. 175 scenarios in 7 slices: Indian English, Hinglish, Hinglish with injected ASR noise, regional Indian English, elderly callers, noisy lines, and callers who keep asking for a person. Labels are written in code. The guard was written from the RBI rules and my unit tests and frozen in a commit before any collections call was run; it was not tuned on data.

## Results

Test split, 79 scenarios. Cells are k/n, rate, [Wilson 95% interval].

| | Baseline agent | Agent + guard |
|---|---|---|
| Self-harm, distress, bereavement, harassment: stopped and escalated | 14/16 = 88% [64%, 97%] | 16/16 = 100% [81%, 100%] |
| Stop request, wrong number, call outside 8 AM to 7 PM: ended without collecting | 4/10 = 40% [17%, 69%] | 10/10 = 100% [72%, 100%] |
| Needed a human and got one | 21/29 = 72% [54%, 85%] | 28/29 = 97% [83%, 99%] |
| ...within the policy turn | 21/29 = 72% [54%, 85%] | 26/29 = 90% [74%, 96%] |
| Hard negatives wrongly stopped or escalated | 0/6 = 0% [0%, 39%] | 0/6 = 0% [0%, 39%] |
| Routine calls transferred without need | 0/24 = 0% [0%, 14%] | 1/24 = 4% [1%, 20%] |
| Promise captured with both amount and date asked for | 7/12 = 58% [32%, 81%] | 11/12 = 92% [65%, 99%] |

Guard rule time: median 0.9 ms per caller turn.

## Three findings

1. **The baseline ignored the calling-hours rule every time.** It was told the local time and told that recovery calls are only allowed 8 AM to 7 PM, and still carried on collecting in all 4 out-of-hours test calls. A one-line clock check in code fixed all 4. Rules that can be checked by code should not be left to the prompt.
2. **Handoff again was the weak spot.** As in the GP domain, the baseline did not transfer callers whose amount, date of birth or account digits kept being garbled; the two-failure counter in the guard did.
3. **The guard cost little on these cases but its precision is barely tested.** It made one unneeded transfer (a noisy Hinglish hard negative counted as two failed captures) and no false stops. Only 6 hard negatives survived data checking, so the false-escalation interval is wide (0% to 39%).

## Limits, plainly

- Synthetic text, scripted callers, my own baseline prompt; nothing here describes any real product.
- **No dispute cases in the results.** The data checker rejected every "already paid" and "wrong amount" transcript (it seems to have counted the planned dispute as an unplanned trigger) and there was no time for rewrite rounds. 52 of 175 transcripts were dropped in total, so groups are smaller than planned (test: 16 must-escalate, 10 compliance, 6 hard negatives).
- No manual spot check of the collections transcripts was done, unlike the GP domain.
- Rules come from RBI circulars of 12 Aug 2022 and 24 Apr 2008 and an RBI draft of 12 Feb 2026 (bereavement); the self-harm and stop-request handling are my design choices. Not legal or compliance advice.
