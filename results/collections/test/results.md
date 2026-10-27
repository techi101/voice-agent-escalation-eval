# Results: Indian loan EMI reminder / collection calls, test split (79 scenarios)
Agent model: gemini-3.1-flash-lite. Cells: k/n = rate [Wilson 95% interval]. Higher is better except false escalation, unneeded transfer and turns.
## Overall
| mode | Must-escalate recall (self-harm, distress, bereavement, harassment) | Compliance stop (stop request, wrong number, 8am-7pm) | Dispute logged, not pressed | Human handoff recall | Handoff within policy turn | False stop/escalation (hard negatives) | Hard negatives handled as routine | Unneeded transfer (routine + hard neg) | Follow-up completeness (amount and date) | Mean caller turns until handoff |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 14/16 = 88% [64%, 97%] | 4/10 = 40% [17%, 69%] | n/a | 21/29 = 72% [54%, 85%] | 21/29 = 72% [54%, 85%] | 0/6 = 0% [0%, 39%] | 6/6 = 100% [61%, 100%] | 0/24 = 0% [0%, 14%] | 7/12 = 58% [32%, 81%] | 1.67 |
| guard | 16/16 = 100% [81%, 100%] | 10/10 = 100% [72%, 100%] | n/a | 28/29 = 97% [83%, 99%] | 26/29 = 90% [74%, 96%] | 0/6 = 0% [0%, 39%] | 5/6 = 83% [44%, 97%] | 1/24 = 4% [1%, 20%] | 11/12 = 92% [65%, 99%] | 2.0 |

## Must-escalate recall (self-harm, distress, bereavement, harassment) by slice
| group | baseline | guard |
|---|---|---|
| elderly | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] |
| hinglish | n/a | n/a |
| hinglish_asr_noise | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] |
| human_repeat | 0/1 = 0% [0%, 79%] | 1/1 = 100% [21%, 100%] |
| indian_english | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] |
| noisy_line | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] |
| regional_indian | 2/3 = 67% [21%, 94%] | 3/3 = 100% [44%, 100%] |

## Compliance stop (stop request, wrong number, 8am-7pm) by slice
| group | baseline | guard |
|---|---|---|
| elderly | 0/2 = 0% [0%, 66%] | 2/2 = 100% [34%, 100%] |
| hinglish | 0/1 = 0% [0%, 79%] | 1/1 = 100% [21%, 100%] |
| hinglish_asr_noise | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| human_repeat | n/a | n/a |
| indian_english | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| noisy_line | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] |
| regional_indian | 0/2 = 0% [0%, 66%] | 2/2 = 100% [34%, 100%] |

## Dispute logged, not pressed by slice
| group | baseline | guard |
|---|---|---|
| elderly | n/a | n/a |
| hinglish | n/a | n/a |
| hinglish_asr_noise | n/a | n/a |
| human_repeat | n/a | n/a |
| indian_english | n/a | n/a |
| noisy_line | n/a | n/a |
| regional_indian | n/a | n/a |

## Human handoff recall by slice
| group | baseline | guard |
|---|---|---|
| elderly | 2/4 = 50% [15%, 85%] | 4/4 = 100% [51%, 100%] |
| hinglish | 3/4 = 75% [30%, 95%] | 4/4 = 100% [51%, 100%] |
| hinglish_asr_noise | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |
| human_repeat | 7/8 = 88% [53%, 98%] | 8/8 = 100% [68%, 100%] |
| indian_english | 2/4 = 50% [15%, 85%] | 3/4 = 75% [30%, 95%] |
| noisy_line | 2/4 = 50% [15%, 85%] | 4/4 = 100% [51%, 100%] |
| regional_indian | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |

## Handoff within policy turn by slice
| group | baseline | guard |
|---|---|---|
| elderly | 2/4 = 50% [15%, 85%] | 3/4 = 75% [30%, 95%] |
| hinglish | 3/4 = 75% [30%, 95%] | 4/4 = 100% [51%, 100%] |
| hinglish_asr_noise | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |
| human_repeat | 7/8 = 88% [53%, 98%] | 8/8 = 100% [68%, 100%] |
| indian_english | 2/4 = 50% [15%, 85%] | 2/4 = 50% [15%, 85%] |
| noisy_line | 2/4 = 50% [15%, 85%] | 4/4 = 100% [51%, 100%] |
| regional_indian | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |

## False stop/escalation (hard negatives) by slice
| group | baseline | guard |
|---|---|---|
| elderly | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] |
| hinglish | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] |
| hinglish_asr_noise | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] |
| human_repeat | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] |
| indian_english | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| noisy_line | n/a | n/a |
| regional_indian | n/a | n/a |

## Hard negatives handled as routine by slice
| group | baseline | guard |
|---|---|---|
| elderly | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| hinglish | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| hinglish_asr_noise | 1/1 = 100% [21%, 100%] | 0/1 = 0% [0%, 79%] |
| human_repeat | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| indian_english | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] |
| noisy_line | n/a | n/a |
| regional_indian | n/a | n/a |

## Unneeded transfer (routine + hard neg) by slice
| group | baseline | guard |
|---|---|---|
| elderly | 0/4 = 0% [0%, 49%] | 0/4 = 0% [0%, 49%] |
| hinglish | 0/4 = 0% [0%, 49%] | 0/4 = 0% [0%, 49%] |
| hinglish_asr_noise | 0/4 = 0% [0%, 49%] | 1/4 = 25% [5%, 70%] |
| human_repeat | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] |
| indian_english | 0/5 = 0% [0%, 43%] | 0/5 = 0% [0%, 43%] |
| noisy_line | 0/3 = 0% [0%, 56%] | 0/3 = 0% [0%, 56%] |
| regional_indian | 0/3 = 0% [0%, 56%] | 0/3 = 0% [0%, 56%] |

## Follow-up completeness (amount and date) by slice
| group | baseline | guard |
|---|---|---|
| elderly | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| hinglish | 0/2 = 0% [0%, 66%] | 2/2 = 100% [34%, 100%] |
| hinglish_asr_noise | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] |
| human_repeat | n/a | n/a |
| indian_english | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] |
| noisy_line | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| regional_indian | 1/2 = 50% [9%, 91%] | 1/2 = 50% [9%, 91%] |

## Turns to handoff, paired (calls handed off in both modes)
| mode | n pairs | baseline mean turns | mode mean turns |
|---|---|---|---|
| guard | 21 | 1.67 | 1.67 |

## Latency
| mode | guard median ms/turn (rules) | guard p95 ms/turn (rules) | guard LLM classifier s/turn | agent LLM calls | agent mean s/call |
|---|---|---|---|---|---|
| baseline | nan | nan | 0.00 | 192 | 4.70 |
| guard | 0.739 | 1.749 | 0.00 | 125 | 2.91 |
