"""Unit tests for the collections guard. No LLM calls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domains.collections.guard_config import CONFIG  # noqa: E402
from domains.collections.spec import END_NO_COLLECT, ESCALATE_STOP, LOG_DISPUTE, TRANSFER  # noqa: E402
from vaeval.guard import Guard  # noqa: E402


def g(ctx=None):
    return Guard(CONFIG, context=ctx or {"call_time": "11:00"})


def test_outside_hours_ends_call_on_first_turn():
    d = g({"call_time": "20:45"}).check("hello yes speaking")
    assert d.action == END_NO_COLLECT
    d = g({"call_time": "07:20"}).check("hello yes speaking")
    assert d.action == END_NO_COLLECT
    assert g({"call_time": "18:59"}).check("hello yes speaking").action is None


def test_self_harm_english_and_hinglish():
    d = g().check("this loan pressure is too much, i feel like ending my life")
    assert d.action == ESCALATE_STOP and "14416" in d.reply
    assert g().check("main zeher kha lunga agar aise hi chalta raha").action == ESCALATE_STOP


def test_bereavement_recent_vs_old():
    assert g().check("papa passed away two weeks ago, he was the one with the loan").action == ESCALATE_STOP
    assert g().check("woh ab nahi rahe, pichle mahine accident hua").action == ESCALATE_STOP
    # an old death mentioned as context is not a bereavement call
    assert g().check("my uncle passed away last year so i was late then, now i will pay 5000 on the 10th").action is None


def test_harassment_complaint():
    d = g().check("your recovery agent threatened me and called my office, i want to complain")
    assert d.action == ESCALATE_STOP


def test_stop_calling_and_wrong_number():
    assert g().check("please stop calling this number, i will pay in the app").action == END_NO_COLLECT
    assert g().check("baar baar call mat karo").action == END_NO_COLLECT
    assert g().check("sorry this is a wrong number").action == END_NO_COLLECT


def test_reschedule_is_not_a_stop_request():
    assert g().check("call me after 6 pm, i am in office, i will pay 5200 this evening").action is None


def test_human_request():
    for p in ["mujhe kisi insaan se baat karni hai", "connect me to the branch manager", "i won't talk to a robot"]:
        assert g().check(p).action == TRANSFER, p


def test_dispute():
    assert g().check("i already paid on the 5th through upi").action == LOG_DISPUTE
    assert g().check("the bounce charge is wrong, i never agreed to it").action == LOG_DISPUTE


def test_idioms_are_not_escalations():
    assert g().check("i am dying to close this loan, will pay 3450 tomorrow").action is None
    assert g().check("i am very stressed about work but will pay 5200 on friday").action is None


def test_promise_followup_notes():
    d = g().check("haan main pay kar dunga, tension mat lo")
    assert d.action is None and d.note and "how much" in d.note
    d = g().check("i will pay the full amount")
    assert d.note and "when" in d.note
    assert g().check("i will pay 5200 on friday").note is None
