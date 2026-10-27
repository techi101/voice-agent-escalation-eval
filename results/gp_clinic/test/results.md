# Results: UK GP clinic phone line, test split (50 scenarios)
Agent model: gemini-3.5-flash-lite. Cells: k/n = rate [Wilson 95% interval]. Higher is better except false escalation, unneeded transfer and turns.
## Overall
| mode | Red-flag escalation recall | Human handoff recall | Handoff within policy turn | False escalation (hard negatives) | Unneeded transfer (routine + hard neg) | Follow-up completeness | Mean caller turns until handoff |
|---|---|---|---|---|---|---|---|
| baseline | 17/17 = 100% [82%, 100%] | 8/16 = 50% [28%, 72%] | 8/16 = 50% [28%, 72%] | 0/7 = 0% [0%, 35%] | 1/17 = 6% [1%, 27%] | n/a | 1.38 |
| guard | 17/17 = 100% [82%, 100%] | 15/16 = 94% [72%, 99%] | 13/16 = 81% [57%, 93%] | 0/7 = 0% [0%, 35%] | 1/17 = 6% [1%, 27%] | n/a | 2.2 |

## Red-flag escalation recall by slice
| group | baseline | guard |
|---|---|---|
| code_mixed | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |
| non_native | 5/5 = 100% [57%, 100%] | 5/5 = 100% [57%, 100%] |
| older_rambling | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| regional | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] |
| standard | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |

## Human handoff recall by slice
| group | baseline | guard |
|---|---|---|
| code_mixed | 2/4 = 50% [15%, 85%] | 3/4 = 75% [30%, 95%] |
| non_native | 2/4 = 50% [15%, 85%] | 4/4 = 100% [51%, 100%] |
| older_rambling | n/a | n/a |
| regional | 2/4 = 50% [15%, 85%] | 4/4 = 100% [51%, 100%] |
| standard | 2/4 = 50% [15%, 85%] | 4/4 = 100% [51%, 100%] |

## Handoff within policy turn by slice
| group | baseline | guard |
|---|---|---|
| code_mixed | 2/4 = 50% [15%, 85%] | 3/4 = 75% [30%, 95%] |
| non_native | 2/4 = 50% [15%, 85%] | 4/4 = 100% [51%, 100%] |
| older_rambling | n/a | n/a |
| regional | 2/4 = 50% [15%, 85%] | 2/4 = 50% [15%, 85%] |
| standard | 2/4 = 50% [15%, 85%] | 4/4 = 100% [51%, 100%] |

## False escalation (hard negatives) by slice
| group | baseline | guard |
|---|---|---|
| code_mixed | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] |
| non_native | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| older_rambling | n/a | n/a |
| regional | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |
| standard | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] |

## Unneeded transfer (routine + hard neg) by slice
| group | baseline | guard |
|---|---|---|
| code_mixed | 0/3 = 0% [0%, 56%] | 0/3 = 0% [0%, 56%] |
| non_native | 1/4 = 25% [5%, 70%] | 1/4 = 25% [5%, 70%] |
| older_rambling | n/a | n/a |
| regional | 0/5 = 0% [0%, 43%] | 0/5 = 0% [0%, 43%] |
| standard | 0/5 = 0% [0%, 43%] | 0/5 = 0% [0%, 43%] |

## Follow-up completeness by slice
| group | baseline | guard |
|---|---|---|
| code_mixed | n/a | n/a |
| non_native | n/a | n/a |
| older_rambling | n/a | n/a |
| regional | n/a | n/a |
| standard | n/a | n/a |

## Turns to handoff, paired (calls handed off in both modes)
| mode | n pairs | baseline mean turns | mode mean turns |
|---|---|---|---|
| guard | 8 | 1.38 | 1.38 |

## Latency
| mode | guard median ms/turn (rules) | guard p95 ms/turn (rules) | guard LLM classifier s/turn | agent LLM calls | agent mean s/call |
|---|---|---|---|---|---|
| baseline | nan | nan | 0.00 | 122 | 5.06 |
| guard | 1.149 | 3.984 | 0.00 | 81 | 5.86 |
