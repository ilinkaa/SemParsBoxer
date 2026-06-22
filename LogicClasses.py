# Class definitions for the logical classes we will need to implement the Lambda calculus part of Lambda-DRS

from dataclasses import dataclass
from typing import Any


@dataclass
class Var:
    """Defines the variable type, this introduces the references"""
    name: str
    # __repr__ auto-generated: Var(name='X')

@dataclass
class Lambda:
    """Lambda class with two arguments, variable and body"""
    leftside: Any
    rightside: Any
    # __repr__ auto-generated: Lambda(leftside=..., rightside=...)

@dataclass
class App:
    """Application class"""
    leftside: Any
    rightside: Any
    # __repr__ auto-generated: App(leftside=..., rightside=...)

@dataclass
class Merge:
    leftside: Any
    rightside: Any
    # __repr__ auto-generated: Merge(leftside=..., rightside=...)

class Predicate:
    """Predicate class, takes a symbol (meaning) and a list of variables"""
    def __init__(self, symbol: str, variables: list):
        self.sym = symbol
        for i, child in enumerate(variables):
            setattr(self, f"variable_{i}", child)

    def _variables(self):
        """Collect all variable_N attributes in order."""
        result = []
        i = 0
        while hasattr(self, f"variable_{i}"):
            result.append(getattr(self, f"variable_{i}"))
            i += 1
        return result

    def __repr__(self):
        vars_repr = ", ".join(repr(v) for v in self._variables())
        return f"Predicate(symbol={self.sym!r}, variables=[{vars_repr}])"




    def __eq__(self, other):
        return isinstance(other, Predicate) and self.sym == other.sym and self._variables() == other._variables()
    

class Relation:
    """Functionnally the same as the Predicate class, but is meant as an equivalent for eq,rel, etc in Prolog"""
    def __init__(self, symbol: str, variables: list):
        self.sym = symbol
        for i, child in enumerate(variables):
            setattr(self, f"variable_{i}", child)

    def _variables(self):
        """Collect all variable_N attributes in order."""
        result = []
        i = 0
        while hasattr(self, f"variable_{i}"):
            result.append(getattr(self, f"variable_{i}"))
            i += 1
        return result

    def __repr__(self):
        vars_repr = ", ".join(repr(v) for v in self._variables())
        return f"Predicate(symbol={self.sym!r}, variables=[{vars_repr}])"