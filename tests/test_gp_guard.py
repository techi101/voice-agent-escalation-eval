"""Unit tests for the GP clinic guard and red-flag rules. No LLM calls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domains.gp_clinic.guard_config import CONFIG  # noqa: E402
from domains.gp_clinic.noise import CONFUSIONS  # noqa: E402
from domains.gp_clinic.spec import ADVISE_111, ADVISE_999, TRANSFER  # noqa: E402
from vaeval.asr_noise import add_noise  # noqa: E402
from vaeval.guard import Guard as _Guard  # noqa: E402


def Guard():  # noqa: N802
    return _Guard(CONFIG)


class redflags:  # noqa: N801  (keeps the old test wording)
    match = staticmethod(CONFIG.matcher.match)


def cats(text):
    return {h.category for h in redflags.match(text)}


def test_stroke_face_and_speech():
    assert "stroke_face" in cats("my husband's mouth has gone droopy on one side this morning")
    assert "stroke_speech" in cats("my words are coming out all wrong since i woke up")


def test_chest_pain_code_mixed():
    assert "chest_pain" in cats("mere seene mein bahut dard ho raha hai abhi")
    assert "chest_pain" in cats("crushing pain in my chest going down my arm")


def test_fuzzy_asr_spelling():
    # small misspellings from speech-to-text still match
    assert "breathing" in cats("i cant breth properly, struggling to breathe right now")


def test_history_is_not_a_red_flag():
    assert cats("my dad had a stroke last year and his speech is a bit slurred, i need his repeat") == set()
    assert cats("i had a heart attack in 2020 and chest pain since then is fine, just need a review") == set()


def test_history_with_new_symptom_still_fires():
    assert "stroke_arm" in cats("he had a stroke years ago but suddenly this morning his arm went numb and weak")


def test_mental_health_level():
    hits = redflags.match("i keep having thoughts of killing myself")
    assert hits and hits[0].level == "mh"


def test_guard_red_flag_overrides_everything():
    g = Guard()
    d = g.check("i want a real person, my face has dropped on one side since an hour ago")
    assert d.action == ADVISE_999
    assert "999" in d.reply and "put you through" in d.reply  # still offers the human


def test_guard_mental_health_111():
    d = Guard().check("i feel there is no point living and i keep thinking of ending it")
    assert d.action == ADVISE_111
    assert "option 2" in d.reply


def test_human_request_never_blocked():
    for phrase in ["can i speak to a receptionist please", "i don't want to speak to you",
                   "put me through to someone", "human", "operator", "kisi insaan se baat karao"]:
        assert Guard().check(phrase).action == TRANSFER, phrase


def test_two_failed_captures_hand_off():
    g = Guard()
    assert g.check("hello it's pizza johnson").action is None
    assert g.check("no i said peter johnson", "Sorry, could you repeat your name?").action is None
    d = g.check("no peter peter johnson", "Sorry, I didn't catch that. Could you spell it?")
    assert d.action == TRANSFER and g.failed_captures == 2


def test_followup_note_for_unnamed_prescription():
    d = Guard().check("hi i need my repeat prescription please it's run out")
    assert d.action is None and d.note and "which medicine" in d.note
    d2 = Guard().check("hi i need my repeat of amlodipine please")
    assert d2.note is None


def test_routine_passes():
    d = Guard().check("hello i'd like to book an appointment about my knee, it's been sore for a few weeks")
    assert d.action is None


def test_noise_deterministic():
    a = add_noise("my chest is very tight and painful right now", 0.3, "x", CONFUSIONS)
    b = add_noise("my chest is very tight and painful right now", 0.3, "x", CONFUSIONS)
    assert a == b
