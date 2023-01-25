from dataclasses import dataclass


@dataclass(frozen=True)
class Sym:
    n: str

@dataclass(frozen=True)
class Nil:
    def __iter__(self): yield from ()

@dataclass(frozen=True)
class Cons:
    hd: 'Any'
    tl: 'Cons | Nil'

    def __iter__(self):
        xs = self
        while isinstance(xs, Cons):
            yield xs.hd
            xs = xs.tl

@dataclass(frozen=True)
class Vec:
    xs: tuple


def eval_expr(form, env):
    # We elide the error checking here for brevity
    match form:
        case Cons(Sym('fn'), Cons(Vec() as params, Cons(body, Nil()))):
            return Fn(params.xs, body, env)

        case Cons(Sym('if'), Cons(predicate, Cons(consequent, Cons(alternative, Nil())))):
            if eval_expr(predicate, env):
                return eval_expr(consequent, env)
            return eval_expr(alternative, env)

        case Cons(procedure_form, argument_forms):
            procedure = eval_expr(procedure_form, env)
            args = [eval_expr(arg, env) for arg in argument_forms]
            return procedure(*args)
        case Nil() as nil:
            return nil
        case Sym(_) as sym:
            return env[sym]
        case None | True | False | int() | float() | str() as value:
            return value
        case x if callable(x):
            return x
    raise Exception(f'invalid form: {form}')


@dataclass
class Fn:
    params: tuple
    body: 'Any'
    env: 'Mapping'

    def __call__(self, *args):
        env = self.env | dict(zip(self.params, args, strict=True))
        return eval_expr(self.body, env)


initial_env = {
    Sym('+'): lambda a, b: a + b,
    Sym('-'): lambda a, b: a - b,
    Sym('*'): lambda a, b: a * b,
    Sym('/'): lambda a, b: a / b,
    Sym('<'): lambda a, b: a < b,
    Sym('>'): lambda a, b: a > b,
}

# (+ 1 2) -> 3
eval_expr(Cons(Sym('+'), Cons(1, Cons(2, Nil()))), initial_env)

# (if (< 1 2) true false) -> true
eval_expr(Cons(Sym('if'), Cons(Cons(Sym('<'), Cons(1, Cons(2, Nil()))), Cons(True, Cons(False, Nil())))), initial_env)

# (fn [a b] (* a b)) -> Fn(...)
eval_expr(Cons(Sym('fn'), Cons(Vec((Sym('a'), Sym('b'))), Cons(Cons(Sym('*'), Cons(Sym('a'), Cons(Sym('b'), Nil()))), Nil()))), initial_env)

# ((fn [a] (* a 11)) 7)  -> 11
eval_expr(Cons(Cons(Sym('fn'), Cons(Vec((Sym('a'),)), Cons(Cons(Sym('*'), Cons(Sym('a'), Cons(11, Nil()))), Nil()))), Cons(7, Nil())), initial_env)
