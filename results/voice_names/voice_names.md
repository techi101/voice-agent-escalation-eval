# Voice slice: full-name capture (20 synthetic names x 2 line conditions)

Exact full-name match, k/n = rate [Wilson 95%]. TTS voices (US English), not real speakers. The name list holds the 20 callers plus 40 similar-sounding distractors.

| condition | raw ASR | + name-list prompt | + prompt and fuzzy match to list | matched to the WRONG registered patient |
|---|---|---|---|---|
| phone | 9/20 = 45% [26%, 66%] | 7/20 = 35% [18%, 57%] | 10/20 = 50% [30%, 70%] | 9/20 = 45% [26%, 66%] |
| speakerphone | 0/20 = 0% [0%, 16%] | 4/20 = 20% [8%, 42%] | 5/20 = 25% [11%, 47%] | 12/20 = 60% [39%, 78%] |
