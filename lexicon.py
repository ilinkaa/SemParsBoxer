# Lexicon corresponding to different CCG categories 
# Because of the limited time, only a handlful of categories are implement (none introducing presupposition triggers)
# All the entries here are adapted from Boxer's lex folder
# https://github.com/valeriobasile/learningbyreading/tree/fc035a2726331d9b3b5019d8772571e300636241/ext/candc/src/prolog/boxer/lex

from LogicClasses import *
from DRSClasses import *


class Counter:
    """
    A counter that auto-increments each time its value is read.
    """



    
    def __init__(self, initial_value=0):
        self._value = initial_value
    
    def get(self):
        self._value += 1
        return self._value
    
_counter = Counter()
_assigned: set[str] = set()


def unique_variable(pattern=None, ignore=None):
    global _counter, _assigned 
    prefix = pattern.name[0].lower() if pattern is not None else "z"
    ignore = (ignore or set()) | _assigned  # never reuse anything assigned before
    while True:
        v = Var(f"{prefix}{_counter.get()}")
        if v.name not in ignore:
            _assigned.add(v.name)           # register as used gl
            return v
        
def reset_counter():
    """Call this between parses to reset variable numbering."""
    global _counter, _assigned
    _counter = Counter()
    _assigned = set()
    
def pos_to_tense_aspect(pos: str) -> tuple[str, str]:
    return {
        "VBZ": ("PRE", "simple"),
        "VBP": ("PRE", "simple"),
        "VBD": ("PAS", "simple"),
        "VBG": ("PRE", "progressive"),
        "VBN": ("PAS", "perfect"),     # or PAS/simple depending on context
        "VB":  ("PRE", "simple"),
        "MD":  ("PRE", "simple"),
    }.get(pos, ("PRE", "simple"))

def make_tense(tense: str):
    """Tense DRS """  
    

    n = unique_variable(pattern=Var("n"))   # Now
    t = unique_variable(pattern=Var("t"))   # Topic 

    if tense == "PRE":   # simple present VBZ/VBP
        return Lambda(Var("S"), Lambda(Var("F"),
            App(Var("S"), Lambda(Var("E"),
                Merge(
                    DRS(DRSrefs([n, t]),
                        DRSconditions([
                            Predicate("now",         [n]),
                            Predicate("temp_included",[Var("E"), t]),
                            Predicate("eq",          [t, n])
                        ])
                    ),
                    App(Var("F"), Var("E"))
                )
            ))
        ))

    elif tense == "PAS":  # simple past VBD
        return Lambda(Var("S"), Lambda(Var("F"),
            App(Var("S"), Lambda(Var("E"),
                Merge(
                    DRS(DRSrefs([n, t]),
                        DRSconditions([
                            Predicate("now",        [n]),
                            Predicate("temp_before", [t, n]),
                            Predicate("temp_included",[Var("E"), t])
                        ])
                    ),
                    App(Var("F"), Var("E"))
                )
            ))
        ))

    elif tense == "FUT":  # future will/shall
        return Lambda(Var("S"), Lambda(Var("F"),
            App(Var("S"), Lambda(Var("E"),
                Merge(
                    DRS(DRSrefs([n, t]),
                        DRSconditions([
                            Predicate("now",        [n]),
                            Predicate("temp_after",  [t, n]),
                            Predicate("temp_included",[Var("E"), t])
                        ])
                    ),
                    App(Var("F"), Var("E"))
                )
            ))
        ))

    else:
        return Lambda(Var("S"), Lambda(Var("F"),
            App(Var("S"), Lambda(Var("E"),
                App(Var("F"), Var("E"))
            ))
        ))
    

def make_aspect(aspect: str, tense_drs: DRS) :
    """Aspect DRS"""
    st = unique_variable(pattern=Var("s")) 

    if aspect == "simple":
        return tense_drs

    elif aspect == "progressive":
        st = unique_variable(pattern=Var("s"))
        return Lambda(Var("S"), Lambda(Var("F"),
        App(App(tense_drs,
            Lambda(Var("E"),
                App(Var("S"), Lambda(Var("E2"),
                    Merge(
                        DRS(DRSrefs([st]), DRSconditions([
                            Predicate("temp_includes", [Var("T"), st]),
                            Predicate("temp_abut",     [Var("E2"), st])
                        ])),
                        App(Var("F"), Var("E2"))
                    )
                ))
            )),
            Var("F")
        )
    ))

    elif aspect == "perfect":  
        return Lambda(Var("S"), Lambda(Var("F"),
            App(tense_drs, Lambda(Var("S2"), Lambda(Var("F2"),
                App(Var("S"), Lambda(Var("E"),
                    Merge(
                        DRS(DRSrefs([st]),
                            DRSconditions([
                                Predicate("temp_before",   [st, Var("T")]),
                                Predicate("temp_abut",     [Var("E"), st])
                            ])
                        ),
                        App(Var("F"), Var("E"))
                    )
                ))
            )))
        ))

    else:
        return tense_drs


def make_tdrs(tense: str, aspect: str):
    """Combine tense and aspect into a single TDRS
    that gets passed into the verb lambda."""
    tense_layer  = make_tense(tense)
    return make_aspect(aspect, tense_layer)



# Note both transitive and intransitive definitions are taken from the standard case 


def make_intransitive_verb(sym: str, pos):
    e    = unique_variable(pattern=Var("e"))
    tense, aspect = pos_to_tense_aspect(pos)
    tdrs = make_tdrs(tense, aspect)
    return Lambda(Var("NP"),
        App(tdrs, Lambda(Var("P"),
            App(Var("NP"), Lambda(Var("X"),
                Merge(
                    DRS(DRSrefs([e]),
                        DRSconditions([
                            Predicate(sym,   [e]),
                            Relation("Actor", [e, Var("X")])
                        ])
                    ),
                    App(Var("P"), e)
                )
            ))
        ))
    )


# Aux 
def make_be_aux(pos):
    tense, aspect = pos_to_tense_aspect(pos)
    tdrs = make_tdrs(tense, aspect)
    return Lambda(Var("VP"), Lambda(Var("NP"),
        App(tdrs, App(Var("VP"), Var("NP")))
    ))


#   Transitive (np V np) extensional

def semlex_not():
    V, Q, F, X, P = Var("B"), Var("H"), Var("C"), Var("D"), Var("M")
    return Lambda(V, Lambda(Q, Lambda(F,
        App(Q, Lambda(X,
            DRS(DRSrefs([]),
                DRSconditions([
                    Negation(
                        App(App(V, Lambda(P, App(P, X))), F)
                    )
                ]))
        ))
    )))

def make_transitive_verb(sym: str,pos) :
    tense, aspect = pos_to_tense_aspect(pos)
    e    = unique_variable(pattern=Var("e"))
    tdrs = make_tdrs(tense, aspect)
    return Lambda(Var("NP2"), Lambda(Var("NP1"),
        App(tdrs, Lambda(Var("P"),
            App(Var("NP1"), Lambda(Var("X"),
                App(Var("NP2"), Lambda(Var("Y"),
                    Merge(
                        DRS(DRSrefs([e]),
                            DRSconditions([
                                Predicate(sym,     [e]),
                                Relation("Actor",  [e, Var("X")]),
                                Relation("Theme",[e, Var("Y")])
                            ])
                        ),
                        App(Var("P"), e)
                    )
                ))
            ))
        ))
    ))

# Lemma argumetn here to match with the mapping
def make_be_progressive_aux():
    VP, NP = Var("VP"), Var("NP")
    return Lambda(VP, Lambda(NP,
        App(Var("VP"), Var("NP"))
    ))

def make_noun(sym:str):
    return Lambda(Var("X"),DRS(DRSrefs([]), DRSconditions([Predicate(sym, [Var("X")])])))

def make_proper_name(lemma: str, 
                  
                     source: str = "nam"):

    x = unique_variable(pattern=Var("x"))
    d = unique_variable(pattern=Var("d"))

    return Lambda(Var("P"),
        Merge(
            DRS(
                DRSrefs([x, d]),
                DRSconditions([
                    Predicate("Named", [d, Var(lemma) 
                                       , Var(source)]),
                    Relation("equals",    [x, d])
                ])
            ),
            App(Var("P"), x)
        )
    )

def make_every():
    """Universal quantification, using the Implication DRS pattern (if B1 then B2)"""
    x = unique_variable(pattern=Var("x"))

    return Lambda(
        Var("N"),
        Lambda(
            Var("P"),
            DRS(
                DRSrefs([]),
                DRSconditions([
                    Imp(
                        Merge(
                            DRS(
                                DRSrefs([x]),
                                DRSconditions([])
                            ),
                            App(Var("N"), x)
                        ),
                        App(Var("P"), x)
                    )
                ])
            )
        )
    )


def make_in_pp(prep_str) :
    """Simple PP logical expression (using "in" as the default preposition)"""
    return Lambda(Var("NP"), Lambda(Var("VP"), Lambda(Var("NP1"), Lambda(Var("P"),
        App(Var("NP1"), Lambda(Var("X"),
            App(Var("NP"), Lambda(Var("Y"),
                Merge(
                    App(App(Var("VP"), Lambda(Var("P2"), App(Var("P2"), Var("X")))),
                        Lambda(Var("E"),
                            Merge(
                                DRS(DRSrefs([]),
                                    DRSconditions([
                                        Relation(prep_str, [Var("E"), Var("Y")])
                                    ])
                                ),
                                App(Var("P"), Var("E"))   
                            )
                        )
                    ),
                    DRS(DRSrefs([]), DRSconditions([]))
                )
            ))
        ))
    ))))

def make_existential_np(noun_pred):
    return App(make_a_det(), make_noun(noun_pred))

def make_a_det():
    """Indefinite determiner"""
    fresh = unique_variable()  

    return Lambda(Var("P"), Lambda(Var("Q"),
        Merge(
            Merge(
                DRS(DRSrefs([fresh]), DRSconditions([])),
                App(Var("P"), fresh)
            ),
            App(Var("Q"), fresh)
        )
    ))


# Below implementing CONJ (coordination) for NPs and VPs separately (although we are not checking for type directly here)
# This makes use of the UnionDRS relation

def make_or_vp():
    return Lambda(Var("V1"), Lambda(Var("V2"), Lambda(Var("NP"),
        Union(
            App(Var("V2"), Var("NP")),
            App(Var("V1"), Var("NP"))
        )
    )))

def make_or_np():
    return Lambda(Var("V1"), Lambda(Var("V2"), Lambda(Var("P"),
        Union(
            App(Var("V2"), Var("P")),
            App(Var("V1"), Var("P"))
        )
    )))
def make_and_np() :
    return Lambda(Var("X"), Lambda(Var("Y"), Lambda(Var("P"),
        Merge(
            App(Var("X"), Var("P")),
            App(Var("Y"), Var("P"))
        )
    )))




def make_and_vp():
    return Lambda(Var("X"), Lambda(Var("Y"), Lambda(Var("NP"), Lambda(Var("P"),
        Merge(
            App(App(Var("X"), Var("NP")), Var("P")),
            App(App(Var("Y"), Var("NP")), Var("P"))
        )
    ))))


