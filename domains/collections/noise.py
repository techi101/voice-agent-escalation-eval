"""Collections ASR-noise word lists: sound-alike swaps common for Indian English / Hinglish, and names to mangle."""

CONFUSIONS = {
    "emi": "amy", "payment": "pavement", "loan": "lone", "bank": "bunk", "salary": "celery", "kal": "call",
    "parso": "person", "hazaar": "has are", "hazar": "has are", "paisa": "pizza", "rupees": "ropes",
    "thousand": "thou sand", "fifteen": "fifty", "fifty": "fifteen", "sixteen": "sixty", "friday": "fried",
    "monday": "mundane", "paid": "played", "already": "all ready", "upi": "you pee", "account": "a count",
    "threatened": "threaten", "suicide": "sue side", "marna": "marina", "zeher": "zahir", "passed": "past",
    "died": "dyed", "manager": "manage", "insaan": "in son", "number": "lumber", "wrong": "long",
    "complaint": "compliant", "agent": "urgent", "human": "human's", "dunga": "dunk a", "karunga": "karuna",
    "ramesh": "ramish", "sunil": "sunny", "priya": "pria", "kumar": "come are", "yadav": "ya there",
}
NAMES_TO_MANGLE = ("ramesh", "sunil", "priya", "kumar", "yadav")
