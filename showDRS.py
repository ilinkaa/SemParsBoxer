
# AI GENERATED CODE
# Displays the DRSs in string / box format

from dataclasses import dataclass
from LogicClasses import *
from DRSClasses import *


# ----------------------------
# Helpers
# ----------------------------

def pad_lines(lines, width):
    return [line.ljust(width) for line in lines]


def hstack(left, right, sep=" "):
    h = max(len(left), len(right))

    left_width = max(len(x) for x in left)
    right_width = max(len(x) for x in right)

    left = left + [" " * left_width] * (h - len(left))
    right = right + [" " * right_width] * (h - len(right))

    return [
        l.ljust(left_width) + sep + r
        for l, r in zip(left, right)
    ]


# ----------------------------
# Atomic objects
# ----------------------------

def render_var(v):
    return v.name


def render_predicate(p):
    args = ",".join(render_var(v) for v in p._variables())
    return f"{p.sym}({args})"


# ----------------------------
# DRS box
# ----------------------------

def render_drs_box(drs):
    refs = " ".join(dict.fromkeys(v.name for v in drs.leftside._variables()))

    conds = []

    for c in drs.rightside._variables():
        conds.extend(render(c))

    content_width = max(
        [len(refs)] +
        [len(line) for line in conds] +
        [1]
    )

    top = "┌" + "─" * (content_width + 2) + "┐"
    refline = "│ " + refs.ljust(content_width) + " │"
    sep = "├" + "─" * (content_width + 2) + "┤"

    body = [
        "│ " + line.ljust(content_width) + " │"
        for line in conds
    ]

    bottom = "└" + "─" * (content_width + 2) + "┘"

    return [top, refline, sep, *body, bottom]


# ----------------------------
# Recursive renderer
# ----------------------------

def render(expr):

    if isinstance(expr, DRS):
        return render_drs_box(expr)

    if isinstance(expr, (Predicate, Relation)):
        return [render_predicate(expr)]

    if isinstance(expr, Negation):
        child = render(expr.drs)

        return [
            "¬ " + child[0],
            *["  " + line for line in child[1:]]
        ]

    if isinstance(expr, Union):

        left = render(expr.leftside)
        right = render(expr.rightside)

        mid = max(len(left), len(right)) // 2

        result = hstack(left, right)

        row = result[mid]
        result[mid] = row.replace(" ", " ∪ ", 1)

        return result

    if isinstance(expr, Imp):

        left = render(expr.leftside)
        right = render(expr.rightside)

        h = max(len(left), len(right))

        left_width = max(len(x) for x in left)

        left += [" " * left_width] * (h - len(left))
        right += [""] * (h - len(right))

        mid = h // 2

        out = []

        for i in range(h):
            connector = " → " if i == mid else "   "
            out.append(left[i].ljust(left_width) + connector + right[i])

        return out

    raise TypeError(f"Unknown expression: {type(expr)}")


def drs_to_string(expr):
    return "\n".join(render(expr))