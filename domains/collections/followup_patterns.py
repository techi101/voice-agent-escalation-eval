"""Collections: regexes that detect the agent ASKING for a missing promise amount or date.

Checked by hand on dev calls (see results/collections/spot_check.md).
"""

ASK_PATTERNS = {
    "amount": [
        r"\bhow much\b", r"\bkitn(a|e|i)\b", r"\b(what|which) amount\b",
        r"\b(confirm|tell me|share|mention)\b[^.?]{0,30}\bamount\b",
        r"\b(full|entire|complete|poora|pura)\b[^.?]{0,40}\?",
        r"\bamount\b[^.?]{0,40}\?",
    ],
    "date": [
        r"\bwhen\b", r"\b(which|what) (date|day)\b", r"\bkab\b", r"\bkis (din|tarikh|date)\b", r"\bby when\b",
        r"\b(date|day|tarikh)\b[^.?]{0,40}\?",
    ],
}
