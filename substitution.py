import string
from LogicClasses import *
from DRSClasses import *


_counter = 0
_assigned: set[str] = set()  

# Generates fresh variables, keeping track of the previously declared ones
# z prefix for Predicate referents, e for event variables

def fresh_var(avoid: set) -> str:
    global _counter, _assigned
    avoid = avoid | _assigned  
    for c in string.ascii_lowercase:
        if c not in avoid:
            _assigned.add(c)   
            return c
    while True:
        name = f"v{_counter}"
        _counter += 1
        if name not in avoid:
            _assigned.add(name)
            return name
# Recursively checks which variables are free in an expression
def free_vars(expr):
    if isinstance(expr, Var):
        return {expr.name}
    elif isinstance(expr, Lambda):
        return free_vars(expr.rightside) - {expr.leftside.name}
    elif isinstance(expr, Negation):
        return free_vars(expr.drs)


    elif isinstance(expr, (App, Merge, Imp, Union)):
        return free_vars(expr.leftside) | free_vars(expr.rightside)

    
    elif isinstance(expr, DRS):
    
        ref_names = {r.name for r in expr.leftside._variables()}
        cond_free = set()
        for cond in expr.rightside._variables():
            cond_free |= free_vars(cond)
        return cond_free - ref_names
    
    elif isinstance(expr, (Predicate, Relation)):
        result = set()
        for v in expr._variables():
            result |= free_vars(v)   
        return result
    else:
        return set()
    
# Given an expression and a target variable, replace it with an expression 

def substitute(expr, var_name: str, arg):
    if isinstance(expr, Var):
        return arg if expr.name == var_name else expr

    elif isinstance(expr, App):
        return App(
            substitute(expr.leftside, var_name, arg),
            substitute(expr.rightside, var_name, arg)
        )
    

    elif isinstance(expr, Merge):
        return Merge(
            substitute(expr.leftside, var_name, arg),
            substitute(expr.rightside, var_name, arg)
        )

    elif isinstance(expr, Imp):
        return Imp(
            substitute(expr.leftside, var_name, arg),
            substitute(expr.rightside, var_name, arg)
        )

    elif isinstance(expr, Lambda):
        bound = expr.leftside.name

        if bound == var_name:
            return expr                        

        if bound in free_vars(arg):
            fresh = fresh_var(
                free_vars(arg) | free_vars(expr.rightside) | {var_name}
            )
            renamed_body = substitute(expr.rightside, bound, Var(fresh))
            return Lambda(
                Var(fresh),
                substitute(renamed_body, var_name, arg)
            )

        return Lambda(
            expr.leftside,
            substitute(expr.rightside, var_name, arg)
        )

    elif isinstance(expr, DRS):
        ref_names  = {r.name for r in expr.leftside._variables()}
        refs       = list(expr.leftside._variables())
        conditions = list(expr.rightside._variables())

        if var_name in ref_names:
            return expr                         

        arg_free = free_vars(arg)

        for i, ref in enumerate(refs):
            if ref.name in arg_free:
                fresh = fresh_var(
                    arg_free | ref_names | free_vars(expr) | {var_name}
                )
                conditions = [
                    substitute(c, ref.name, Var(fresh)) for c in conditions
                ]
                refs[i] = Var(fresh)

        new_conditions = [substitute(c, var_name, arg) for c in conditions]
        return DRS(DRSrefs(refs), DRSconditions(new_conditions))
    
    elif isinstance(expr, Negation):
        return Negation(drs=substitute(expr.drs, var_name, arg))
    
    elif isinstance(expr, Union):
        return Union(
        substitute(expr.leftside, var_name, arg),
        substitute(expr.rightside, var_name, arg)
    )

    elif isinstance(expr, (Predicate, Relation)):
        new_vars = [substitute(v, var_name, arg) for v in expr._variables()]
        return type(expr)(expr.sym, new_vars)

    else:
        return expr




# Recursively performs beta-reduction by traversing the object's types 

def beta_reduce(expr):
    if isinstance(expr, Var):
        return expr

    elif isinstance(expr, App):
        fn  = beta_reduce(expr.leftside)
        arg = beta_reduce(expr.rightside)

        if isinstance(fn, Lambda):
            reduced = substitute(fn.rightside, fn.leftside.name, arg)
            return beta_reduce(reduced)

    # distribute application into Union branches
        elif isinstance(fn, Union):
            return Union(
            beta_reduce(App(fn.leftside, arg)),
            beta_reduce(App(fn.rightside, arg))
        )

        else:
            return App(fn, arg)
    elif isinstance(expr, Negation):

     
        return Negation(drs = beta_reduce(expr.drs))

    elif isinstance(expr, Lambda):
        return Lambda(expr.leftside, beta_reduce(expr.rightside))

    elif isinstance(expr, Merge):
        return Merge(beta_reduce(expr.leftside), beta_reduce(expr.rightside))
    
    elif isinstance(expr, Imp):
        return Imp(beta_reduce(expr.leftside), beta_reduce(expr.rightside))
    elif isinstance(expr, Union):
        return Union(
        beta_reduce(expr.leftside),
        beta_reduce(expr.rightside)
    )

    elif isinstance(expr, DRS):
        new_conds = [beta_reduce(c) for c in expr.rightside._variables()]
        return DRS(expr.leftside, DRSconditions(new_conds))

    elif isinstance(expr, (Predicate, Relation)):
        new_vars = [beta_reduce(v) for v in expr._variables()]
        return type(expr)(expr.sym, new_vars)

    else:
        return expr
  
     
# Flatten the Merges down to DRS objects, an expression is 
# considering complete when not Apps, Lambda or Merges remain
def flatten_merges(term):
    if isinstance(term, Merge):
        left  = flatten_merges(term.leftside)
        right = flatten_merges(term.rightside)
        
        # if either side is a Negation, it can't be merged into refs/conds directly
        # wrap it as a condition in a DRS with empty refs instead
        if isinstance(left, (Negation, Imp,Union )):
            left = DRS(DRSrefs([]), DRSconditions([left]))
        if isinstance(right,(Negation, Imp,Union )):
            right = DRS(DRSrefs([]), DRSconditions([right]))
      

        return DRS(
            DRSrefs(left.leftside._variables() + right.leftside._variables()),
            DRSconditions(left.rightside._variables() + right.rightside._variables())
        )
    if isinstance(term, Negation):
        return Negation(flatten_merges(term.drs))

    if isinstance(term, Union):
        return Union(flatten_merges(term.leftside), flatten_merges(term.rightside))
    if isinstance(term, Imp):
        return Imp(flatten_merges(term.leftside), flatten_merges(term.rightside))
    if isinstance(term, DRS):
        new_conds = [flatten_merges(c) for c in term.rightside._variables()]
        return DRS(term.leftside, DRSconditions(new_conds))
    return term