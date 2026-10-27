# Results: UK GP clinic phone line, dev split (80 scenarios)
Agent model: gemini-3.5-flash-lite. Cells: k/n = rate [Wilson 95% interval]. Higher is better except false escalation, unneeded transfer and turns.
## Overall
| mode | Red-flag escalation recall | Human handoff recall | Handoff within policy turn | False escalation (hard negatives) | Unneeded transfer (routine + hard neg) | Follow-up completeness | Mean caller turns until handoff |
|---|---|---|---|---|---|---|---|
| baseline | 29/30 = 97% [83%, 99%] | 11/20 = 55% [34%, 74%] | 11/20 = 55% [34%, 74%] | 0/15 = 0% [0%, 20%] | 1/30 = 3% [1%, 17%] | 9/10 = 90% [60%, 98%] | 1.64 |
| guard | 30/30 = 100% [89%, 100%] | 19/20 = 95% [76%, 99%] | 19/20 = 95% [76%, 99%] | 0/15 = 0% [0%, 20%] | 1/30 = 3% [1%, 17%] | 10/10 = 100% [72%, 100%] | 2.05 |

## Red-flag escalation recall by slice
| group | baseline | guard |
|---|---|---|
| asr_noise | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |
| code_mixed | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |
| fragmented | 3/4 = 75% [30%, 95%] | 4/4 = 100% [51%, 100%] |
| human_repeat | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] |
| non_native | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |
| older_rambling | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |
| regional | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |
| standard | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |

## Human handoff recall by slice
| group | baseline | guard |
|---|---|---|
| asr_noise | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| code_mixed | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| fragmented | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| human_repeat | 5/6 = 83% [44%, 97%] | 6/6 = 100% [61%, 100%] |
| non_native | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| older_rambling | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| regional | 0/2 = 0% [0%, 66%] | 1/2 = 50% [9%, 91%] |
| standard | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |

## Handoff within policy turn by slice
| group | baseline | guard |
|---|---|---|
| asr_noise | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| code_mixed | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| fragmented | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| human_repeat | 5/6 = 83% [44%, 97%] | 6/6 = 100% [61%, 100%] |
| non_native | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| older_rambling | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |
| regional | 0/2 = 0% [0%, 66%] | 1/2 = 50% [9%, 91%] |
| standard | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] |

## False escalation (hard negatives) by slice
| group | baseline | guard |
|---|---|---|
| asr_noise | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| code_mixed | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| fragmented | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| human_repeat | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] |
| non_native | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| older_rambling | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| regional | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| standard | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |

## Unneeded transfer (routine + hard neg) by slice
| group | baseline | guard |
|---|---|---|
| asr_noise | 0/4 = 0% [0%, 49%] | 0/4 = 0% [0%, 49%] |
| code_mixed | 0/4 = 0% [0%, 49%] | 0/4 = 0% [0%, 49%] |
| fragmented | 0/4 = 0% [0%, 49%] | 0/4 = 0% [0%, 49%] |
| human_repeat | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| non_native | 0/4 = 0% [0%, 49%] | 0/4 = 0% [0%, 49%] |
| older_rambling | 0/4 = 0% [0%, 49%] | 0/4 = 0% [0%, 49%] |
| regional | 1/4 = 25% [5%, 70%] | 1/4 = 25% [5%, 70%] |
| standard | 0/4 = 0% [0%, 49%] | 0/4 = 0% [0%, 49%] |

## Follow-up completeness by slice
| group | baseline | guard |
|---|---|---|
| asr_noise | 0/1 = 0% [0%, 79%] | 1/1 = 100% [21%, 100%] |
| code_mixed | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| fragmented | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| human_repeat | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| non_native | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| older_rambling | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| regional | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] |
| standard | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] |

## Turns to handoff, paired (calls handed off in both modes)
| mode | n pairs | baseline mean turns | mode mean turns |
|---|---|---|---|
| guard | 11 | 1.64 | 1.64 |

## Latency
| mode | guard median ms/turn (rules) | guard p95 ms/turn (rules) | guard LLM classifier s/turn | agent LLM calls | agent mean s/call |
|---|---|---|---|---|---|
| baseline | nan | nan | 0.00 | 199 | 10.84 |
| guard | 0.663 | 3.453 | 0.00 | 140 | 7.51 |
