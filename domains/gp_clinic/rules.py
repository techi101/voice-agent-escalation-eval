"""GP clinic red-flag rules for the shared matcher (vaeval/matcher.py).

How it works, in plain terms:
  1. Clean the text: lowercase, keep letters/numbers/apostrophes only.
  2. Each red-flag rule is a PAIR of word lists, A and B. The rule fires when a
     word from A and a word from B appear within `window` words of each other.
     Example: A = {chest, chhati, seene}, B = {pain, dard, tight, crushing}.
  3. Words are compared with fuzzy matching (rapidfuzz ratio), so small ASR
     spelling errors still match ("breething" ~ "breathing").
  4. A hit is ignored if the words around it talk about the past
     ("last year", "since my stroke two years ago") and nothing around it says
     it is happening now ("suddenly", "this morning", "right now").

Word lists come from the wording of public nhs.uk pages (see the
URLs in spec.py) plus common romanised Hindi/Urdu/Punjabi/Bengali terms. They were tuned
on the DEV split only. They are not clinically validated and not complete.
"""
from __future__ import annotations

# category -> (action level, [ (A words, B words, window) ... ])
# action level: "999" or "mh" (mental health crisis: 111 option 2, 999 if immediate)
RULES: dict[str, tuple[str, list[tuple[set, set, int]]]] = {
    "stroke_face": ("999", [
        ({"face", "mouth", "smile", "eye", "chehra", "muh", "munh", "mooh", "mukh"},
         {"dropped", "drooping", "droopy", "droop", "lopsided", "fallen", "slipped", "sagging", "twisted",
          "tedha", "tehra", "tera", "latak", "lataka", "dheela", "one", "side", "wonky", "crooked", "jhuk"}, 4),
    ]),
    "stroke_arm": ("999", [
        ({"arm", "arms", "hand", "leg", "side", "baazu", "bazu", "baah", "baahn", "haath", "hath", "bahu", "haat"},
         {"numb", "weak", "floppy", "lift", "dead", "heavy", "paralysed", "sunn", "sun", "kamzor", "bejaan",
          "uthta", "utha", "chalda", "chal", "deadweight", "tingling", "useless", "drop", "dropped"}, 5),
    ]),
    "stroke_speech": ("999", [
        ({"speech", "words", "word", "talking", "speak", "speaking", "talk", "voice", "zubaan", "zabaan",
          "zuban", "bol", "boli", "gal", "kotha", "lafz", "alfaaz", "shabd"},
         {"slurred", "slurring", "slur", "wrong", "funny", "gibberish", "jumbled", "muddled", "strange",
          "garbled", "nonsense", "find", "cant", "can't", "ladkhada", "ladkhda", "atak", "nahi", "nai",
          "hoyna", "parchi", "sense", "weird", "drunk"}, 7),
        # a strong single word plus a "this is happening now" word nearby
        ({"slurred", "slurring", "gibberish"}, {"today", "suddenly", "sudden", "morning", "woke", "hour", "hours",
          "minutes", "new", "afternoon", "abhi", "aaj", "achanak"}, 10),
    ]),
    "chest_pain": ("999", [
        ({"chest", "chhati", "chati", "chaati", "seena", "seene", "sina", "sine", "buk", "buke", "bukay", "heart", "dil"},
         {"pain", "pains", "tight", "tightness", "crushing", "pressure", "heavy", "squeezing", "squeeze",
          "dard", "dukh", "byatha", "betha", "batha", "jakad", "bhaari", "bhari", "dabav", "pressing"}, 4),
        ({"pain", "dard", "byatha"}, {"jaw", "neck", "arm", "jabda"}, 6),
    ]),
    "breathing": ("999", [
        ({"breathe", "breath", "breathing", "breathless", "saans", "sans", "saah", "sah", "shash", "shwas",
          "shaas", "dum", "air", "gasping", "gasp"},
         {"cant", "can't", "cannot", "struggling", "fighting", "gasping", "nahi", "nai", "nahin", "taklif",
          "takleef", "kosto", "kashto", "aunda", "auna", "phool", "phoolna", "blue", "sucking", "hard",
          "difficult", "difficulty", "rukk", "ruk", "get"}, 4),
        ({"lips", "lip", "honth", "hont"}, {"blue", "neela", "nila", "grey", "gray"}, 3),
    ]),
    "sepsis": ("999", [
        ({"rash", "spots", "daane", "dane"}, {"fade", "fading", "glass", "press", "pressed", "blanch"}, 6),
        ({"skin", "chamdi", "chamri"}, {"blotchy", "mottled", "blue", "grey", "pale", "neeli"}, 4),
        ({"confused", "confusion", "muddled", "sense", "behki", "bahki", "ulti", "seedhi"},
         {"infection", "temperature", "fever", "bukhar", "jor", "jvar", "uti", "urine", "sepsis", "fast", "floppy"}, 10),
        ({"floppy", "limp", "unresponsive", "behosh", "beyhosh"}, {"baby", "child", "son", "daughter", "bacha", "bachcha", "baccha"}, 6),
    ]),
    "anaphylaxis": ("999", [
        ({"throat", "tongue", "lips", "lip", "face", "gala", "gale", "jeebh", "jeeb", "jeebhi", "honth"},
         {"swelling", "swollen", "swell", "puffing", "closing", "sujan", "soojan", "suj", "phool", "phoola",
          "phul", "fula", "shoja"}, 5),
        ({"swallow", "nigal", "nigalna"}, {"cant", "can't", "hard", "difficult", "nahi"}, 4),
        ({"wheeze", "wheezing", "wheezy"}, {"sting", "stung", "nuts", "nut", "allergic", "allergy", "reaction", "swelling", "swollen"}, 12),
    ]),
    "suicide_immediate": ("999", [
        ({"taken", "took", "swallowed", "kha", "khayi", "khali", "li", "le", "kheye", "kheyechi", "khaye", "khaaye"},
         {"tablets", "pills", "overdose", "goli", "goliyan", "golian", "dawai", "boshudh"}, 5),
        ({"bridge", "jump", "cut", "cutting", "kaat"}, {"end", "die", "kill", "marna", "mar", "want", "wants", "badly"}, 8),
    ]),
    "suicide_thoughts": ("mh", [
        ({"kill", "killing", "end", "ending", "die", "suicide", "suicidal", "khudkushi", "khud", "marna",
          "mar", "jaan", "zindagi", "jeena", "morte", "marte", "atmahatya", "bachte", "banchte"},
         {"myself", "herself", "himself", "it", "life", "want", "wants", "thoughts", "thinking", "chahta",
          "chahti", "dena", "deni", "point", "nahi", "ichha", "iccha", "lagda", "safe", "living"}, 4),
        ({"no", "nahi"}, {"point"}, 2),
    ]),
}

PAST = {"last", "ago", "years", "year", "since", "had", "history", "used", "recovering", "recovered",
        "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "pehle", "notnew", "saal", "purana",
        "months", "stable", "better", "fine"}
NOW = {"now", "today", "suddenly", "sudden", "morning", "afternoon", "tonight", "minutes", "hour", "hours",
       "started", "abhi", "aaj", "achanak", "hune", "ekhon", "aj", "right", "woke"}
