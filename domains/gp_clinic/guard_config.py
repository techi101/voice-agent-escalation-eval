"""GP clinic guard configuration (word lists, fixed replies, follow-up checks).

Tuned on the dev split only. Frozen in git commit ea2f56a (then named
gpeval/guard.py) before any test-split run; this file is the same logic moved
into the domain folder.
"""
from vaeval.guard import FollowupCheck, GuardConfig, PatternStage
from vaeval.matcher import Matcher

from .rules import NOW, PAST, RULES
from .spec import ADVISE_111, ADVISE_999, TRANSFER

REPLY_999 = ("What you have described could be an emergency. Please hang up and call 999 now. "
             "If you cannot do that, stay on the line and I will put you through to the reception team straight away.")
REPLY_MH = ("Thank you for telling me. You do not have to deal with this alone. If you or someone else is in "
            "immediate danger, please call 999 now. Otherwise you can call NHS 111 and choose option 2 for urgent "
            "mental health help. I can also put you through to a member of the team now.")
REPLY_TRANSFER = "Of course. I am putting you through to a member of the reception team now."
REPLY_TRANSFER_FAILS = ("I'm sorry, I'm not getting this right. I am putting you through to a member of the "
                        "reception team now so you do not have to repeat yourself.")

HUMAN_PATTERNS = [
    r"\b(speak|talk|speaking|talking|put me through|transfer me|connect me)\b.{0,25}\b(someone|somebody|person|human|"
    r"receptionist|reception|staff|operator|real|actual|member of)\b",
    r"\b(real|actual|proper|live)\s+(person|human|people|receptionist)\b",
    r"\bhuman\b", r"\boperator\b", r"\breceptionist\b", r"\bput me (through|to)\b", r"\btransfer me\b",
    r"\b(don'?t|do not|dont)\s+want\s+to\s+(speak|talk)\s+to\s+(you|a computer|a robot|a machine|the ai|an ai|this)\b",
    r"\b(not|no)\s+(a\s+)?(robot|machine|computer)\b",
    r"\b(insaan|insan|banda|bande|kisi\s+(se|naal|insaan)|manush|manushe|admi|aadmi)\b",
]
CLARIFY_PATTERNS = [
    r"\bsorry\b", r"didn'?t (quite )?catch", r"did not catch", r"could you (please )?(repeat|say that again|spell)",
    r"say that again", r"\bpardon\b", r"(couldn'?t|could not|didn'?t|did not) (quite )?(understand|hear|get)",
    r"\bspell\b", r"one more time", r"\bapologi[sz]e", r"\bapologies\b", r"\bconfirm\b.{0,30}\b(again|correct)\b",
]
CORRECTION_PATTERNS = [
    r"^\W*(no+|nah|nope|nae|naw|na)\b", r"\bi said\b", r"\b(that'?s|thats|that is) (not|wrong)\b", r"\bnot (pizza|that)\b",
    r"\bwrong\b", r"\bnot listening\b", r"\bagain\b", r"\bnot right\b", r"\b(garbled|nonsense|mumbling)\b",
    r"\b(na na|nahi nahi|nai nai)\b", r"\b(galat|ghalat|bhul|bhool|abar|dobara|phir se)\b",
]
RX_PATTERNS = [r"\bprescription", r"\brepeat\b", r"\bmedic", r"\bmedicine", r"\btablets?\b", r"\bdawai", r"\bdavai",
               r"\bdawa\b", r"\bousud", r"\bossudh", r"\bpills?\b", r"\brun out\b", r"\bran out\b"]
RESULTS_PATTERNS = [r"\bresults?\b", r"\breport\b", r"\bnateeja", r"\bnatija", r"\bresult\b"]
MEDICINES = {"amlodipine", "salbutamol", "metformin", "sertraline", "inhaler", "ventolin", "atorvastatin", "statin",
             "ramipril", "omeprazole", "levothyroxine", "insulin", "warfarin", "aspirin", "paracetamol", "epipen",
             "lisinopril", "bisoprolol", "citalopram", "gabapentin", "amoxicillin", "antibiotics", "co-codamol",
             "naproxen", "simvastatin", "lansoprazole", "fluoxetine", "inhalers", "cream", "patches"}
TESTS = {"blood", "x-ray", "xray", "scan", "smear", "urine", "ecg", "mri", "ultrasound", "biopsy", "swab", "cholesterol"}

LLM_SYSTEM = ("You screen one caller utterance to a GP surgery phone line. Do not give advice. "
              "Return JSON {\"emergency_999\": bool, \"mental_health_crisis\": bool, \"wants_human\": bool}. "
              "emergency_999 is true only for possible NHS 999 signs happening NOW: stroke signs (face drooping, "
              "arm weakness, new speech difficulty), chest pain, severe breathing difficulty, sepsis signs, "
              "anaphylaxis, or someone who has harmed themselves or is about to. Past or stable problems are false. "
              "mental_health_crisis is true for suicidal thoughts without immediate danger. "
              "wants_human is true if the caller asks for a person.")

CONFIG = GuardConfig(
    matcher=Matcher(RULES, PAST, NOW, span=12),
    level_actions={"999": (ADVISE_999, REPLY_999, "red flag {cat} ({a}~{b})"),
                   "mh": (ADVISE_111, REPLY_MH, "mental health crisis ({a}~{b})")},
    level_priority=["999", "mh"],
    stages=[PatternStage("human requested", HUMAN_PATTERNS, TRANSFER, REPLY_TRANSFER)],
    clarify_patterns=CLARIFY_PATTERNS,
    correction_patterns=CORRECTION_PATTERNS,
    transfer_action=TRANSFER,
    reply_transfer_fails=REPLY_TRANSFER_FAILS,
    followups=[
        FollowupCheck("medication_name", RX_PATTERNS,
                      "The caller has not said which medicine they need. Before finishing, ask which medicine (name and strength if they know it).",
                      named_tokens=MEDICINES),
        FollowupCheck("test_name", RESULTS_PATTERNS,
                      "The caller has not said which test the results are for. Before finishing, ask which test and roughly when it was done.",
                      named_tokens=TESTS),
    ],
    llm_system=LLM_SYSTEM,
    llm_labels={"emergency_999": (ADVISE_999, REPLY_999, "llm classifier: emergency"),
                "mental_health_crisis": (ADVISE_111, REPLY_MH, "llm classifier: mental health"),
                "wants_human": (TRANSFER, REPLY_TRANSFER, "llm classifier: human")},
)
