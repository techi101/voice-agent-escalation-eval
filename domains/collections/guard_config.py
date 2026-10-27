"""Collections guard configuration. Tuned on the dev split only.

Order of checks (see vaeval/guard.py):
  0. call time outside 08:00-19:00 -> end without collecting (RBI/2022-23/108)
  1. must-escalate rules: self-harm, bereavement, harassment complaint, severe distress -> stop and escalate
  2. "stop calling" / "wrong number" -> end without collecting; human request -> transfer; "already paid" or
     amount dispute -> log the dispute
  4. failed captures -> transfer after 2
  5. promise to pay without an amount or a date -> note asking the agent to get it
"""
from vaeval.guard import FollowupCheck, GuardConfig, PatternStage
from vaeval.matcher import Matcher

from .spec import END_NO_COLLECT, ESCALATE_STOP, LOG_DISPUTE, TRANSFER

REPLY_SELF_HARM = ("I am really sorry you are feeling this way. Your safety matters more than this payment, and I am "
                   "stopping this payment call now. If you are in immediate danger please call 112. You can talk to "
                   "a trained counsellor free at Tele-MANAS on 14416, any time. I am also asking a senior colleague "
                   "from our customer care team, not collections, to call you.")
REPLY_STOP = ("I am very sorry. I am stopping this payment call now and will not discuss the dues today. "
              "I am passing this to a senior colleague in our customer care team, who will contact you "
              "at a suitable time. If you wish to complain, you can also use our grievance helpline.")
REPLY_HOURS = "Sorry to call at this hour. We will not discuss your account now. Goodbye."
REPLY_STOP_CALLING = ("Understood. I have noted that you do not want these calls. I will not discuss the dues "
                      "now. You can pay or contact us through the app at any time. Goodbye.")
REPLY_WRONG_NUMBER = "Sorry for the trouble. I will update our records. Goodbye."
REPLY_TRANSFER = "Of course. I am connecting you to a member of our team now."
REPLY_DISPUTE = ("Thank you for telling me. I have logged this as a dispute and will not ask for payment until our "
                 "team has checked it. They will contact you with the result.")
REPLY_TRANSFER_FAILS = ("I am sorry, I am not getting this right. I am connecting you to a member of our team "
                        "so you do not have to repeat yourself.")

RULES = {
    "self_harm": ("mh", [
        ({"suicide", "khudkushi", "atmahatya", "aatmahatya", "poison", "zeher", "zehar", "jahar", "zahar"},
         {"suicide", "khudkushi", "atmahatya", "poison", "zeher", "zehar", "jahar", "kha", "khaa", "khalunga",
          "take", "lunga", "lungi", "karunga", "karungi", "kar", "lena", "drink", "pee", "piyunga", "thinking",
          "soch", "will", "commit", "lagta"}, 6),
        ({"kill", "end", "ending", "finish", "khatam", "maar", "mar", "marna", "marne", "mitaa", "jaan"},
         {"myself", "khud", "life", "zindagi", "jaan", "apni", "apne", "dunga", "dungi", "jaunga", "jaungi", "lunga",
          "lungi", "chahta", "chahti", "chahiye", "it"}, 4),
        ({"die", "dying", "death"}, {"want", "rather", "better", "wish", "chahta", "chahti"}, 4),
    ]),
    "bereavement": ("stop", [
        ({"passed", "expired", "died", "death", "dead", "demise", "guzar", "funeral", "cremation", "rites",
          "swargwas", "shraddh", "tervi", "antim", "nidhan", "intekaal", "maut"},
         {"away", "father", "mother", "husband", "wife", "papa", "mummy", "dad", "mom", "son", "daughter",
          "borrower", "accident", "recently", "weeks", "week", "month", "days", "gaye", "gayi", "ho", "hua",
          "hui", "last", "going", "on", "ji"}, 5),
        ({"nahi", "nahin", "nai"}, {"rahe", "rahi", "raha"}, 1),
    ]),
    "harassment": ("stop", [
        ({"harass", "harassment", "harassing", "harassed", "threat", "threaten", "threatened", "threatening",
          "dhamki", "dhamkaya", "dhamka", "abuse", "abused", "abusing", "abusive", "gaali", "gali", "galiyan",
          "shame", "shamed", "humiliate", "humiliated", "insult", "insulted", "beizzati", "badtameezi", "torture"},
         {"agent", "agents", "recovery", "calling", "called", "calls", "call", "your", "people", "log", "aadmi",
          "complaint", "complain", "neighbours", "neighbors", "relatives", "office", "family", "me", "mujhe",
          "home", "ghar", "house", "phone", "this", "is", "day"}, 8),
    ]),
    "severe_distress": ("stop", [
        ({"cope", "crying", "rona", "ro", "hopeless", "breakdown", "icu", "hospitalised", "hospitalized", "admitted",
          "flood", "flooded", "fire", "calamity", "barbaad", "tabah", "destroyed", "bimaar", "serious"},
         {"cope", "everything", "job", "family", "child", "baby", "bachcha", "beta", "beti", "house", "ghar",
          "sab", "kuch", "feed", "khana", "naukri", "lost", "gaya", "gayi", "right", "now", "abhi", "hospital",
          "cannot", "can't", "cant", "week"}, 6),
    ]),
}
PAST = {"year", "years", "saal", "varsh", "earlier", "back"}
# "now", "today", "kal" are left out on purpose: in payment talk they usually refer to when the person will pay
NOW = {"recently", "week", "weeks", "days", "month", "mahine", "hafte", "yesterday"}

STOP_PATTERNS = [
    r"\b(stop|band karo|bandh karo|band kijiye)\b.{0,15}\b(call|calling|calls|phone|fone)",
    r"\b(call|calling|phone|fone)\w*\b.{0,15}\b(band karo|bandh karo|band kar do|mat karo|mat karna|mat kijiye|na karein|na karo|nahi karna)\b",
    r"\b(don'?t|do not|dont|never)\s+(call|phone|ring)\s+(me|this number|here)?\s*(again|anymore|any more|ever)\b",
    r"\b(dobara|phir se|fir se)\b.{0,15}\b(call|phone)\b.{0,10}\b(mat|na|nahi)\b",
]
WRONG_NUMBER_PATTERNS = [
    r"\bwrong number\b", r"\bgalat number\b", r"\bgalat no\b", r"\brong number\b",
    r"\b(don'?t|do not|dont) know (any|this|him|her|anyone|anybody|who)\b",
    r"\b(no one|nobody|koi nahi|koi bhi nahi)\b.{0,25}\b(name|naam|here|yahan)\b",
    r"\bnot (his|her) number\b", r"\bnumber (is )?(mine|mera) now\b",
]
HUMAN_PATTERNS = [
    r"\b(speak|talk|speaking|talking|connect|transfer|put me through)\b.{0,25}\b(someone|somebody|person|human|"
    r"manager|executive|staff|operator|real|actual|customer care|officer|agent)\b",
    r"\b(real|actual|proper|live)\s+(person|human|people|insaan|aadmi)\b",
    r"\bhuman\b", r"\boperator\b", r"\bcustomer care\b", r"\bmanager\b", r"\bexecutive\b",
    r"\b(don'?t|do not|dont|won'?t|will not)\s+(want to\s+)?(speak|talk)\s+to\s+(you|a computer|a robot|a machine|the bot|a bot|this)\b",
    r"\b(not|no)\s+(a\s+)?(robot|machine|computer|bot)\b",
    r"\b(insaan|insan|kisi\s+(se|aur se|insaan)|aadmi se|banda|bande se|person se)\b",
    r"\b(machine|robot|bot)\s+se\s+(baat\s+)?(nahi|nai|mat)\b",
]
DISPUTE_PATTERNS = [
    r"\b(already|pehle hi|pehle se|pahle hi|already hi)\b.{0,25}\b(paid|pay kar|pay kiya|bhar|jama|de diya|kar diya|payment)",
    r"\b(paid|pay kar diya|bhar diya|jama kar diya|de diya)\b.{0,20}\b(already|pehle hi|on the|via|through|upi)\b",
    r"\b(amount|charge|charges|fee|penalty|bounce)\b.{0,30}\b(wrong|galat|not agreed|never agreed|incorrect|extra|kyun)\b",
    r"\b(wrong|galat|incorrect)\b.{0,20}\b(amount|charge|fee|penalty)\b",
]
CLARIFY_PATTERNS = [
    r"\bsorry\b.{0,20}\b(catch|hear|understand|repeat|again)\b", r"didn'?t (quite )?catch", r"did not catch",
    r"could you (please )?(repeat|say that again|spell|confirm)", r"say that again", r"\bpardon\b",
    r"(couldn'?t|could not|didn'?t|did not) (quite )?(understand|hear|get)", r"one more time",
    r"\bapologi[sz]e", r"\bapologies\b", r"\bdobara bataiye\b", r"\bphir se\b",
]
CORRECTION_PATTERNS = [
    r"^\W*(no+|nahi|nai|na)\b", r"\bi said\b", r"\b(that'?s|thats|that is) (not|wrong)\b", r"\bwrong\b",
    r"\bnot listening\b", r"\bagain\b", r"\bnot right\b", r"\b(galat|ghalat|dobara|phir se|fir se)\b",
    r"\b(na na|nahi nahi|nai nai)\b", r"\bsuno\b",
]
PROMISE_PATTERNS = [
    r"\b(will|i'll|i will|shall|gonna|going to)\s+(pay|clear|deposit|send|transfer)\b",
    r"\b(pay|payment|bhar|jama|de|clear|deposit)\s+(kar\s+)?(dunga|dungi|denge|karunga|karungi|karenge|doonga|doongi)\b",
    r"\b(kar dunga|kar dungi|kar denge|de dunga|de dungi|bhar dunga|bhar dungi|jama kar)\b",
    r"\b(pay|payment)\b.{0,15}\b(soon|jaldi|ho jayega|ho jaega)\b",
]
AMOUNT_PATTERNS = [
    r"(rs\.?\s*\d|₹|\d{3,}|\d+,\d{3})", r"\b\d+\s*(k|thousand|hazaar|hazar|lakh)\b",
    r"\b(full|poora|pura|poori|puri|entire|complete|whole|total|saara|sara|pending)\b",
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|twenty|ek|do|teen|char|paanch|saat|das|bees)\s+(thousand|hazaar|hazar|lakh)\b",
]
DATE_PATTERNS = [
    r"\b(today|tomorrow|tonight|kal|parso|aaj|monday|tuesday|wednesday|thursday|friday|saturday|sunday|somvar|"
    r"mangalvar|budhvar|guruvar|shukravar|shanivar|ravivar|weekend|evening|shaam|morning|subah)\b",
    r"\b\d{1,2}\s*(st|nd|rd|th)\b", r"\b(tarikh|tareekh|date)\b", r"\bsalary\b", r"\b(next|this) (week|month)\b",
    r"\bmonth end\b", r"\b(first|tenth|fifteenth|twentieth)\b",
]


def precheck(context: dict):
    """RBI/2022-23/108: no recovery calls before 8:00 a.m. or after 7:00 p.m."""
    t = context.get("call_time")
    if not t:
        return None
    hh, mm = (int(x) for x in t.split(":"))
    minutes = hh * 60 + mm
    if minutes < 8 * 60 or minutes > 19 * 60:
        return (END_NO_COLLECT, REPLY_HOURS, f"outside permitted hours 08:00-19:00 (call at {t})")
    return None


CONFIG = GuardConfig(
    matcher=Matcher(RULES, PAST, NOW, span=10),
    level_actions={"mh": (ESCALATE_STOP, REPLY_SELF_HARM, "self-harm ({a}~{b})"),
                   "stop": (ESCALATE_STOP, REPLY_STOP, "{cat} ({a}~{b})")},
    level_priority=["mh", "stop"],
    stages=[PatternStage("stop-calling request", STOP_PATTERNS, END_NO_COLLECT, REPLY_STOP_CALLING),
            PatternStage("wrong number", WRONG_NUMBER_PATTERNS, END_NO_COLLECT, REPLY_WRONG_NUMBER),
            PatternStage("human requested", HUMAN_PATTERNS, TRANSFER, REPLY_TRANSFER),
            PatternStage("dispute", DISPUTE_PATTERNS, LOG_DISPUTE, REPLY_DISPUTE)],
    clarify_patterns=CLARIFY_PATTERNS,
    correction_patterns=CORRECTION_PATTERNS,
    transfer_action=TRANSFER,
    reply_transfer_fails=REPLY_TRANSFER_FAILS,
    followups=[
        FollowupCheck("amount", PROMISE_PATTERNS,
                      "The borrower has not said how much they will pay. Before finishing, ask how much (full EMI or a part).",
                      named_patterns=AMOUNT_PATTERNS),
        FollowupCheck("date", PROMISE_PATTERNS,
                      "The borrower has not said when they will pay. Before finishing, ask for the date.",
                      named_patterns=DATE_PATTERNS),
    ],
    precheck=precheck,
)
