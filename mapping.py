from typing import Any, Callable
from lexicon import *
from LogicClasses import *
from DRSClasses import *

def normalize_cat(cat: str) -> str:
    return cat.replace(" ", "")

def parse_ner_type(entity: str) -> str:
    return {
        "I-ORG": "org", "B-ORG": "org",
        "I-PER": "per", "B-PER": "per",
        "I-LOC": "loc", "B-LOC": "loc",
        "I-GPE": "loc", "B-GPE": "loc",
        "I-MISC":"nam", "B-MISC":"nam",
    }.get(entity, "per")

# closing argument — discharges final tense P
closing = Lambda(Var("_"), DRS(DRSrefs([]), DRSconditions([])))

# ── LEXICON ────────────────────────────────────────────────────────────────────
# structure: {normalized_cat: {pos: lambda lemma: constructor(...)}}
# "_" as pos key = wildcard fallback for any unmatched POS
# closed class entries dispatch on lemma value inside the lambda
# open class entries pass lemma directly to the constructor

LEXICON: dict[str, dict[str, Callable[[str], Any]]] = {

    # ── NOUNS ──────────────────────────────────────────────────────────────────
    "N": {
        "NN":   lambda lemma: make_noun(lemma),
        "NNS":  lambda lemma: make_noun(lemma),
        "NNP":  lambda lemma: make_proper_name(lemma),
        "NNPS": lambda lemma: make_proper_name(lemma),
        "_":    lambda lemma: make_noun(lemma),
    },
    "N/N": {
        "NN":   lambda lemma: make_noun(lemma),
        "NNS":  lambda lemma: make_noun(lemma),
        "NNP":  lambda lemma: make_proper_name(lemma),
        "NNPS": lambda lemma: make_proper_name(lemma),
        "_":    lambda lemma: make_noun(lemma),
    },

    # ── ADJECTIVES — N/N ───────────────────────────────────────────────────────
    # not implemented yet — placeholder returns noun modifier identity
    # "N/N": { ... }

    # ── DETERMINERS ────────────────────────────────────────────────────────────
    "NP[nb]/N": {
        "DT": lambda lemma: (
            make_a_det()    if lemma in {"a", "an", "some"}             else
            make_every()    if lemma in {"every", "each", "all", "any"} else
            make_a_det()    # fallback — the/no not implemented yet
        ),
        "_":  lambda lemma: make_a_det(),
    },

    "NP/N": {
        "DT": lambda lemma: (
            make_a_det()    if lemma in {"a", "an", "some"}             else
            make_every()    if lemma in {"every", "each", "all", "any"} else
            make_a_det()
        ),
        "_":  lambda lemma: make_a_det(),
    },
    
    "(S[dcl]\\NP)/(S[ng]\\NP)":{
        "VBZ":  lambda lemma: make_be_aux("VBZ"),
        "VBP":  lambda lemma: make_be_aux("VBP"),
        "VBD":  lambda lemma: make_be_aux("VBD"),
        "VBG":  lambda lemma: make_be_aux("VBG"),
        "VBN":  lambda lemma: make_be_aux("VBN"),
        "VB":   lambda lemma: make_be_aux("VB"),
        "_":    lambda lemma: make_be_aux("VBZ"),
        },
        
    "(S[dcl]\\NP)/NP":{
        "VBZ":  lambda lemma: make_be_aux("VBZ"),
        "VBP":  lambda lemma: make_be_aux("VBP"),
        "VBD":  lambda lemma: make_be_aux("VBD"),
        "VBG":  lambda lemma: make_be_aux("VBG"),
        "VBN":  lambda lemma: make_be_aux("VBN"),
        "VB":   lambda lemma: make_be_aux("VB"),
        "_":    lambda lemma: make_be_aux("VBZ"),
        },


    


    # ── INTRANSITIVE VERBS — S\NP ──────────────────────────────────────────────
    "S[dcl]\\NP": {
        "VBZ":  lambda lemma: make_intransitive_verb(lemma, "VBZ"),
        "VBP":  lambda lemma: make_intransitive_verb(lemma, "VBP"),
        "VBD":  lambda lemma: make_intransitive_verb(lemma, "VBD"),
        "VBG":  lambda lemma: make_intransitive_verb(lemma, "VBG"),
        "VBN":  lambda lemma: make_intransitive_verb(lemma, "VBN"),
        "VB":   lambda lemma: make_intransitive_verb(lemma, "VB"),
        "_":    lambda lemma: make_intransitive_verb(lemma, "VBZ"),
    },
    


    # base form after auxiliary
    "S[b]\\NP": {
        "VB":   lambda lemma: make_intransitive_verb(lemma, "VB"),
        "VBG":  lambda lemma: make_intransitive_verb(lemma, "VBG"),
        "_":    lambda lemma: make_intransitive_verb(lemma, "VB"),
    },

    # progressive form
    "S[ng]\\NP": {
        "VBG":  lambda lemma: make_intransitive_verb(lemma, "VBG"),
        "_":    lambda lemma: make_intransitive_verb(lemma, "VBG"),
        "NN":lambda lemma: make_existential_np(lemma)
    },

    # past participle
    "S[pt]\\NP": {
        "VBN":  lambda lemma: make_intransitive_verb(lemma, "VBN"),
        "_":    lambda lemma: make_intransitive_verb(lemma, "VBN"),
    },
    "S[pss]\\NP": {
    "VBN":  lambda lemma: make_intransitive_verb(lemma, "VBN"),
    "_":    lambda lemma: make_intransitive_verb(lemma, "VBN"),
},

    # ── TRANSITIVE VERBS — (S\NP)/NP ───────────────────────────────────────────
    "(S[dcl]\\NP)/NP": {
        "VBZ":  lambda lemma: make_transitive_verb(lemma, "VBZ"),
        "VBP":  lambda lemma: make_transitive_verb(lemma, "VBP"),
        "VBD":  lambda lemma: make_transitive_verb(lemma, "VBD"),
        "VBG":  lambda lemma: make_transitive_verb(lemma, "VBG"),
        "VBN":  lambda lemma: make_transitive_verb(lemma, "VBN"),
        "VB":   lambda lemma: make_transitive_verb(lemma, "VB"),
        "_":    lambda lemma: make_transitive_verb(lemma, "VBZ"),
    },
    "(S[dcl]\\NP)/PP": {
        "VBZ":  lambda lemma: make_transitive_verb(lemma, "VBZ"),
        "VBP":  lambda lemma: make_transitive_verb(lemma, "VBP"),
        "VBD":  lambda lemma: make_transitive_verb(lemma, "VBD"),
        "VBG":  lambda lemma: make_transitive_verb(lemma, "VBG"),
        "VBN":  lambda lemma: make_transitive_verb(lemma, "VBN"),
        "VB":   lambda lemma: make_transitive_verb(lemma, "VB"),
        "_":    lambda lemma: make_transitive_verb(lemma, "VBZ"),
    },
    

    "(S[b]\\NP)/NP": {
        "VB":   lambda lemma: make_transitive_verb(lemma, "VB"),
        "_":    lambda lemma: make_transitive_verb(lemma, "VB"),
    },

    "(S[ng]\\NP)/NP": {
        "VBG":  lambda lemma: make_transitive_verb(lemma, "VBG"),
        "_":    lambda lemma: make_transitive_verb(lemma, "VBG"),
    },

    "(S[pt]\\NP)/NP": {
        "VBN":  lambda lemma: make_transitive_verb(lemma, "VBN"),
        "_":    lambda lemma: make_transitive_verb(lemma, "VBN"),
    },


    "(S[dcl]\\NP)/(S[ng]\\NP)":{
        "VBZ": lambda lemma:  make_be_progressive_aux()
    },

    # ── AUXILIARIES ────────────────────────────────────────────────────────────
    # not implemented as separate make_aux yet —
    # aux + main verb handled via CCG composition (bx/fc rules)
    # the main verb entry already carries tense via pos_to_tense_aspect
    # so aux entries here just pass through as identity for now

    # ── NEGATION — (S\NP)\(S\NP) ───────────────────────────────────────────────
    # not implemented as standalone yet — handled via VP coordination
    # placeholder: make_not() if available, else skip

    # ── PREPOSITIONS — (S\NP)\(S\NP)/NP ───────────────────────────────────────
    "(S[dcl]\\NP)\\(S[dcl]\\NP)/NP": {
        "IN":   lambda lemma: make_in_pp(lemma),
        "TO":   lambda lemma: make_in_pp(lemma),
        "_":    lambda lemma: make_in_pp(lemma),
    },

    "(S[b]\\NP)\\(S[b]\\NP)/NP": {
        "IN":   lambda lemma: make_in_pp(lemma),
        "_":    lambda lemma: make_in_pp(lemma),
    },

    "(S[ng]\\NP)\\(S[ng]\\NP)/NP": {
        "IN":   lambda lemma: make_in_pp(lemma),
        "_":    lambda lemma: make_in_pp(lemma),
    },
    

    # generic PP — catches remaining S\NP variants
    "(S\\NP)\\(S\\NP)/NP": {
        "IN":   lambda lemma: make_in_pp(lemma),
        "TO":   lambda lemma: make_in_pp(lemma),
        "_":    lambda lemma: make_in_pp(lemma),
    },
# prepositions — both paren variants
"((S[dcl]\\NP)\\(S[dcl]\\NP))/NP": {
    "IN":  lambda lemma: make_in_pp(lemma),
    "TO":  lambda lemma: make_in_pp(lemma),
    "_":   lambda lemma: make_in_pp(lemma),
},
"((S[b]\\NP)\\(S[b]\\NP))/NP": {
    "IN":  lambda lemma: make_in_pp(lemma),
    "_":   lambda lemma: make_in_pp(lemma),
},
"((S[ng]\\NP)\\(S[ng]\\NP))/NP": {
    "IN":  lambda lemma: make_in_pp(lemma),
    "_":   lambda lemma: make_in_pp(lemma),
},
# generic fallback — any mood
"((S\\NP)\\(S\\NP))/NP": {
    "IN":  lambda lemma: make_in_pp(lemma),
    "TO":  lambda lemma: make_in_pp(lemma),
    "_":   lambda lemma: make_in_pp(lemma),
},
    # ── COORDINATION ────────────────────────────────────────────────────────────
    # returns a marker tuple — parse_rule dispatches to make_and_*/make_or_*
    # based on result category of the conj rule node
    "conj": {
        "CC":   lambda lemma: ("coord", lemma),
        "IN":   lambda lemma: ("coord", lemma),
        "_":    lambda lemma: ("coord", "and"),
    },
    #NEGATION 
"(S\\NP)\\(S\\NP)":{"RB": lambda lemma : semlex_not()},



    # ── PUNCTUATION ─────────────────────────────────────────────────────────────
    ".": {"_": lambda lemma: closing},
    ",": {"_": lambda lemma: closing},
    ":": {"_": lambda lemma: closing},
    ";": {"_": lambda lemma: closing},
}


def lookup(lemma: str, cat: str, pos: str,
           word: str, entity: str = "O") -> Any:
    """
    Look up semantic entry for a CCG lexical item.
    Priority:
      1. exact (cat, pos) match in LEXICON
      2. wildcard (cat, _) match in LEXICON
      3. proper name — NNP/NNPS or entity tag
      4. bare NP — treat as proper name
      5. punctuation fallback
      6. KeyError
    """
    cat_norm = normalize_cat(cat)

    if cat_norm in LEXICON:
 
        pos_dict = LEXICON[cat_norm]


        # 1. exact pos match
        if pos in pos_dict:
            return pos_dict[pos](lemma)

        # 2. wildcard fallback
        if "_" in pos_dict:
            return pos_dict["_"](lemma)

    # 3. proper name — not caught by N entry above
    if pos in {"NNP", "NNPS"} or (entity != "O" and entity != ""):
        ner_type = parse_ner_type(entity)
        return make_proper_name(lemma, source=ner_type)

    # 4. bare NP with capital — treat as proper name
    if cat_norm in {"NP", "NP[nb]"} and word[0].isupper():
       
        return make_proper_name(lemma)

    # 5. punctuation fallback
    if pos in {".", ",", ":", ";", "``", "''", "PUNCT", "NFP", "-LRB-", "-RRB-"}:
        return closing

    raise KeyError(
        f"No lexicon entry for lemma='{lemma}' "
        f"cat='{cat_norm}' pos='{pos}'"
    )