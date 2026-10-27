"""GP clinic ASR-noise word lists: sound-alike swaps and names to mangle (Peter -> Pizza)."""

CONFUSIONS = {
    "peter": "pizza", "claire": "clear", "tom": "tim", "johnson": "johnston", "bennett": "bonnet",
    "ashworth": "ash worth", "chest": "chess", "pain": "pane", "breathe": "breed", "breathing": "breeding",
    "breath": "bread", "stroke": "stroll", "face": "phase", "arm": "harm", "speech": "peach",
    "speak": "sneak", "words": "worlds", "slurred": "slid", "tablets": "tablet", "prescription": "subscription",
    "appointment": "a point meant", "swelling": "smelling", "throat": "throw", "results": "resorts",
    "tongue": "tong", "numb": "num", "weak": "week", "rash": "rush", "confused": "confuse",
    "dizzy": "busy", "lips": "lisp", "blue": "blew", "tight": "tide", "heart": "hard", "sick": "sik",
    "repeat": "receipt", "doctor": "doctors", "blood": "bud", "pressure": "pleasure", "wheezing": "wheeling",
    "swallow": "swallowed", "drooping": "dropping", "suddenly": "sudden", "collapsed": "collapse",
}

NAMES_TO_MANGLE = ("peter", "claire", "tom", "johnson", "bennett", "ashworth")
