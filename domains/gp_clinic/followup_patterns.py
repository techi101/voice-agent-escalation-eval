"""GP clinic: regexes that detect the agent ASKING for a missing field.

Checked by hand against 20 dev calls (see results/gp_clinic/spot_check.md).
"""

ASK_PATTERNS = {
    "medication_name": [
        r"\b(which|what)\b[^.?]{0,40}\b(medicine|medicines|medication|medications|tablets|prescription|item|items|drug|drugs|inhaler)\b",
        r"\bnames? of\b[^.?]{0,30}\b(medicine|medicines|medication|medications|tablets|drug|drugs)\b",
        r"\b(medicine|medication)s?\b[^.?]{0,30}\b(called|name)\b",
        r"\bwhat (is it|do you need|are you after)\b",
    ],
    "test_name": [
        r"\b(which|what)\b[^.?]{0,40}\b(test|tests|results? (is|are|was|were) (it|they|for)|blood test|scan|investigation)\b",
        r"\bwhat (kind|type) of\b[^.?]{0,20}\b(test|results?)\b",
        r"\bwhat\b[^.?]{0,20}\bresults?\b[^.?]{0,20}\bfor\b",
    ],
}
