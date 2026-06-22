from dataclasses import dataclass
from typing import Any
from LogicClasses import *


class DRSrefs:
    """Stores Var objects, DRS referents"""
    def __init__(self, variables: list):
        for i, child in enumerate(variables):
            setattr(self, f"variable_{i}", child)

    def _variables(self):
        result = []
        i = 0
        while hasattr(self, f"variable_{i}"):
            result.append(getattr(self, f"variable_{i}"))
            i += 1
        return result

    def __repr__(self):
        vars_repr = ", ".join(repr(v) for v in self._variables())
        return f"DRSrefs(variables=[{vars_repr}])"

    def __eq__(self, other):
        return isinstance(other, DRSrefs) and self._variables() == other._variables()


class DRSconditions:
    """Atores DRS condtions (should be of type Predicate, type distinction between DRS refs (which should only have type variable) and DRS conds (which take Predicate, Relations etc) not specified here yet """
    def __init__(self, variables: list):
        for i, child in enumerate(variables):
            setattr(self, f"variable_{i}", child)

    def _variables(self):
        result = []
        i = 0
        while hasattr(self, f"variable_{i}"):
            result.append(getattr(self, f"variable_{i}"))
            i += 1
        return result

    def __repr__(self):
        vars_repr = ", ".join(repr(v) for v in self._variables())
        return f"DRSconditions(variables=[{vars_repr}])"

    def __eq__(self, other):
        return isinstance(other, DRSconditions) and self._variables() == other._variables()


@dataclass
class DRS:
    """DRS object, has two attributes (referents and conditions)"""
    leftside: Any
    rightside: Any

@dataclass
class Negation:
    """Negated DRS, wraps around one DRS"""
    drs : Any


@dataclass
class Imp:
    """Implicature, used for universal quantification"""
    leftside: Any
    rightside: Any

@dataclass
class Union:
    """Union DRS class"""
    leftside: Any  
    rightside: Any


@dataclass

class AlfaDRS(DRS):
    """Tentative AlfaDRS class"""
    pass




@dataclass
class Merge:
    """Merge class, wraps around two DRSs"""
    leftside: Any
    rightside: Any
    # __repr__ auto-generated: Merge(leftside=..., rightside=...)
