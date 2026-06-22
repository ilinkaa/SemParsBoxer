
# Takes a XML file containing CCG derivations as input and parses them according to our lexicon and categories 

import codecs
from parse_sentences import run_pipeline
import xml.etree.ElementTree as ET
from LogicClasses import *
from DRSClasses import *
from mapping import *
from substitution import *
import lexicon 
import showDRS
import substitution 
closing = Lambda(Var("_"), DRS(DRSrefs([]), DRSconditions([])))



def is_np_category(cat_norm: str) -> bool:
    """Checking category to distinguish NP vs VP coordination"""
    c = cat_norm
    while c.startswith("(") and c.endswith(")"):
        depth = 0
        matched = True
        for i, ch in enumerate(c[:-1]):
            if ch == "(": depth += 1
            elif ch == ")": depth -= 1
            if depth == 0:
                matched = False
                break
        if matched:
            c = c[1:-1]
        else:
            break
    return c == "NP" or c.startswith("NP\\") or c.startswith("NP/") or c == "N\\N"


def compose_bx(is_sem, not_sem):
    Obj, Subj = Var("Obj"), Var("Subj")
    return Lambda(Obj, Lambda(Subj,
        App(App(not_sem, App(is_sem, Obj)), Subj)
    ))

def compose_node(node):
    if node.tag == "ccg":
        return compose_node(list(node)[0])

    if node.tag == "lf":
        lemma  = node.attrib["lemma"]
        cat    = node.attrib["cat"]
        pos    = node.attrib["pos"]
        word   = node.attrib["word"]
        entity = node.attrib.get("entity", "O")
      
    
        l = lookup(lemma, normalize_cat(str(cat)), pos, word, entity)
       
      
     
            
        return l

    if node.tag == "rule":
        rule_type = node.attrib["type"]
        children  = [compose_node(i) for i in list(node)]

        if rule_type == "fa":
            return App(children[0], children[1])

        elif rule_type == "ba":
            return App(children[1], children[0])

        elif rule_type in {"fc", "fxc"}:
            return App(children[0], children[1])

        elif rule_type in {"bc", "bx"}:
            return compose_bx(children[0], children[1])  

        elif rule_type == "rp":
            return children[0]              

        elif rule_type == "lp":
            return children[1]

        elif rule_type == "conj":
            coord_marker = children[0]
            right = children[1]
            sym = coord_marker[1] if isinstance(coord_marker, tuple) else "and"
            cat_norm = normalize_cat(node.attrib.get("cat", ""))
            
            
            if is_np_category(cat_norm):
               
                conj = make_and_np() if sym in {"and","but"} else make_or_np()
            elif is_np_category(cat_norm):
                conj = make_and_np() if sym in {"and","but"} else make_or_np()
            else:
                conj = make_and_vp() if sym in {"and","but"} else make_or_vp()
            return App(conj, right)

        elif rule_type == "lex":
            child = children[0]
            parent_cat = normalize_cat(node.attrib.get("cat", ""))
            child_cat  = normalize_cat(list(node)[0].attrib.get("cat", ""))

            if child_cat == "N" and is_np_category(parent_cat):
                temp = make_a_det()
                
                return App(temp, child)   
            return child

        elif rule_type == "tr":
            return children[0]

        else:
            print(f"  warning: unknown rule type '{rule_type}' — defaulting to fa")
            if len(children) == 2:
                return App(children[0], children[1])
            return children[0]

    raise ValueError(f"Unknown node tag: {node.tag}")




def parse_sent_ccg(ccg_der):
    sent =ccg_der.findall(".//lf")
    sent = [s.attrib["word"] for s in sent]
    print(" ".join(sent))
    composed_node = compose_node(ccg_der)
    closed = composed_node
    
    closed = App(composed_node, closing)
  
    b = beta_reduce(closed)
 
    b = flatten_merges(b)
    reset_counter()
    c = showDRS.drs_to_string(b)
    print(c)
    return b


