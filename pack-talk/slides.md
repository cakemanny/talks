---
title:
- Pack - A Lisp in Python
author:
- Daniel Golding
theme:
- Crane
date:
- 26 Jan 2023
---

## Agenda
<!--
Ideas
- show multiple slides for showing macro expansion

-->

- A quick intro to LISP for the unfamiliar
- We talk about how we can interpret a lisp in Python


## LISP - A quick intro for people who have not seen it

::: notes
Ask if people are familiar and skip over if they are
:::

- Created by John McCarthy in 1960
- There are many dialects
  - Scheme <!-- Chez Scheme, Racket, ... -->
  - Common Lisp
  - Clojure
  - Emacs Lisp <!-- TODO check name -->

- Everything is an s-expression.
  - Lists starting with `(` and ending with `)`
- The first item at the beginning on the list is the function name


## LISP - A quick intro for people who have not seen it

### In Python we say...
```python
>>> 1 + 2
3
>>> 2 * 4 + 6 * 8
56
```

### In a LISP we say...
```clojure
user=> (+ 1 2)
3
user=> (+ (* 2 4) (* 6 8))
56
```


## LISP - A quick intro for people who have not seen it

### In Python we say...

```python
>>> def is_valid(age):
...     if age < 0 or age > 129:
...         return True
...     return False
```

### In a LISP we might say...
```clojure
user=> (def valid?
         (fn [age]
          (if (or (< age 0) (> age 129))
           true
           false)))
```

## Pack

- Most ideas based on Clojure
- Namespaces
- Macros
- Python interop ... 

<!-- -->


## Pack - Some Code

_A small demo occurs_ 😱

<!-- See wc-example and flask-example -->

##

So.... how do we go about writing a LISP interpreter

## Parsing

```python
def read_***(input_text):
    ...
    return parsed_***, remaining_text
```
. . .

```python
>>> from pack.interp import read_num
>>> read_num('1 1 2 3 5 8 13')
(1, ' 1 2 3 5 8 13')
```


## Parsing - Identifiers

```python
def is_ident_start(c):
    return (
        'a' <= c <= 'z'
        or 'A' <= c <= 'Z'
        or c in ('+', '-', '*', '/', '<', '>', '!', '=', '&', '_', '.', '?')
        or '🌀' <= c <= '🫸'
    )


def is_ident(c):
    return is_ident_start(c) or (c in ("'")) or '0' <= c <= '9'


def read_ident(text):
    i = 0
    for c in text:
        if is_ident(c):
            i += 1
        else:
            break

    return split_ident(text[:i]), text[i:]
```


## Parsing - Reading Lists

```python
def try_read(text):
    if text == '':
        return Reader.NOTHING, text
    c = text[0]
    ...  # eat whitespace
    c1 = text[1] if text[1:] else ''
    match c:
        case '(' | '[' | '{':
            return read_list(c, text[1:], closer[c])
        case ')' | ']' | '}':
            raise Unmatched(c, text[1:], location_from(text))
    ...
```

## Parsing - Reading Lists

```python
def read_list(opener, text, closing):
    remaining = text
    elements = []
    while True:
        try:
            elem, remaining = try_read(remaining)
            elements.append(elem)
        except Unmatched as unmatched:
            if unmatched.c == closing:
                return close_sequence(opener, elements), unmatched.remaining
            else:
                ... # raise syntax error
```

## Parsing - Reading Lists

```python
def read_list(opener, text, closing):
    remaining = text
    elements = []
    while True:
        try:
            elem, remaining = try_read(remaining)
            if elem is Reader.NOTHING:
                raise Unclosed(opener, location_from(text))
            else:
                elements.append(elem)
        except Unmatched as unmatched:
            if unmatched.c == closing:
                return close_sequence(opener, elements), unmatched.remaining
            else:
                ... # raise syntax error
```

## Parsing - ...

Don't forget

* Numbers
* Strings
* Keywords
* Comments
* Quoted Forms
* Quasi-quoted Forms

## ~~Parsing~~ _Reading_ - Putting it together

```python
def try_read(text):
    if text == '':
        return Reader.NOTHING, text
    c = text[0]
    ...  # eat whitespace
    c1 = text[1] if text[1:] else ''
    match c:
        case '(' | '[' | '{':
            return read_list(c, text[1:], closer[c])
        case ')' | ']' | '}':
            raise Unmatched(c, text[1:], location_from(text))
        case "'":
            return read_quoted(text[1:])
        case '-' | '+' if '0' <= c1 <= '9':
            return read_num(text[1:], c)
        case n if '0' <= n <= '9':
            return read_num(text)
        case '"':
            return read_str(text)
        case ':':
            return read_keyword(text)
        case s if is_ident(s):
            return read_sym(text)
    raise NotImplementedError(c)
```

##

```clojure
user=> (def map
  (fn map [f xs]
    (let* [fcons
           (fn [x ys]
             (cons (f x) ys)]]
             (foldr fcons '() xs))))

SyntaxError("trying to close a '(' with a ']'")
Unmatched(')')
```

. . .

Can you spot where the problem is? 🔍

. . .

I think we need to improve these errors 🤦


## How NOT to implement error handling

- Start by ignoring error handling - it delays the fun
- Run into errors developing
- subclass the builtin python `str` class


## FileString

```python
>>> from pack.reader import FileString
>>> fs = FileString("hello", "a.txt", 1, 0)
>>> fs
a.txt:1:0 'hello'
```

. . .

```python
>>> fs = FileString("African violet\nApple blossom\nCamelia", "flowers.txt", 1, 0)
>>> fs
flowers.txt:1:0 'African violet\nApple blossom\nCamelia'
>>> fs[10:]
flowers.txt:1:10 'olet\nApple blossom\nCamelia'
>>> fs[20:]
flowers.txt:2:5 ' blossom\nCamelia'
>>> fs[30:]
flowers.txt:3:1 'amelia'
```

## FileString - How?

- `str` is immutable - so we must override `__new__` as well as `__init__`
- `s[i:]` - track `'\n'` s between `0` and `i` when the string is sliced

```python
class FileString(str):
    """A string that knows where it came from in a file"""

    def __new__(cls, s, file, lineno, col):
        obj = super().__new__(cls, s)
        obj.__init__(s, file, lineno, col)
        return obj

    def __init__(self, s, file, lineno, col):
        ...  # boilerplate init with super().__init__ call and field setting

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            ... # see '\n', increment lineno, reset col
            return self.__class__(
                super().__getitem__(idx), self.file, lineno, col
            )
        return super().__getitem__(idx)
```

## FileString - Problems we might run into

We might want to use `repr` to get correct quoting, generating code.

```python
    exec(txt, globals, ns)
  File "<string>", line 3
    return __Sym(None, /Users/daniel/src/python/pack-lang/pack/core.pack:110:11 'do')
                       ^
SyntaxError: invalid syntax
```

## Checkpoint - So what have we done so far

```python
>>> from pack.reader import read_all_forms
>>> read_all_forms("(def valid? (fn [age] (if (or (< age 0) (> age 129)) true false)))")[0]
Cons(Sym(None, 'def'),
     Cons(Sym(None, 'valid?'),
          Cons(Cons(Sym(None, 'fn'),
                    Cons(Vec(xs=(Sym(None, 'age'),), height=0),
                         Cons(Cons(Sym(None, 'if'),
                                   Cons(Cons(Sym(None, 'or'),
                                             Cons(Cons(Sym(None, '<'),
                                                       Cons(Sym(None, 'age'),
                                                            Cons(0, Nil()))),
                                                  Cons(Cons(Sym(None, '>'),
                                                            Cons(Sym(None, 'age'),
                                                                 Cons(129, Nil()))),
                                                       Nil()))),
                                        Cons(True,
                                             Cons(False,
                                                  Nil())))),
                              Nil()))),
               Nil())))
```

Ok, we have a reader. How do we make it do... stuff?


## Evaluating

Let's evaluate a small subset of Pack

```
(~procedure ~arg1 ~arg2 ...)
(fn [~p1 ~p2 ...] ~body)
(if ~pred ~cons ~alt)
```

i.e. we should be able to evaluate all of these

```
(+ 1 2)
(print "λx.x")

(fn [x y] ((+ (* x x) y)))

(if (< a b) a b)
```

## Evaluating - Some Data Constructors

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Sym:
    n: str
```

## Evaluating - Some Data Constructors

```python
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
```


## Evaluating - Some Data Constructors

```python
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
```


## Evaluating

```python
def eval_expr(form, env):
    match form:
        ...
```

## Evaluating

```python
def eval_expr(form, env):
    match form:
        ...
        case Nil() as nil:
            return nil
        case Sym(_) as sym:
            return env[sym]
        case None | True | False | int() | float() | str() as value:
            return value
        case x if callable(x):
            return x
```

## Evaluating

```python
def eval_expr(form, env):
    match form:
        ...
        case Cons(procedure_form, argument_forms):
            procedure = eval_expr(procedure_form, env)
            args = [eval_expr(arg, env) for arg in argument_forms]
            return procedure(*args)
        ...
```

## Evaluating

```python
def eval_expr(form, env):
    match form:
        ...
        case Cons(Sym('if'), Cons(predicate, Cons(consequent, Cons(alternative, Nil())))):
            if eval_expr(predicate, env):
                return eval_expr(consequent, env)
            return eval_expr(alternative, env)
        ...
```

## Evaluating

```python
def eval_expr(form, env):
    match form:
        case Cons(Sym('fn'), Cons(Vec() as params, Cons(body, Nil()))):
            return Fn(params.xs, body, env)

        ...

@dataclass
class Fn:
    params: tuple
    body: 'Any'
    env: 'Mapping'

    def __call__(self, *args):
        env = self.env | dict(zip(self.params, args, strict=True))
        return eval_expr(self.body, env)
```

## Evaluating

```python
def eval_expr(form, env):
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
```

## Evaluating

```python
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
```

##

```python
>>> # (+ 1 2) -> 3
>>> eval_expr(Cons(Sym('+'), Cons(1, Cons(2, Nil()))), initial_env)
3
```

. . .

```python
>>> # (if (< 1 2) true false) -> true
>>> eval_expr(Cons(Sym('if'), Cons(Cons(Sym('<'), Cons(1, Cons(2, Nil()))), Cons(True, Cons(False, Nil())))), initial_env)
True
```

. . .

```python
>>> # (fn [a b] (* a b)) -> Fn(...)
>>> eval_expr(Cons(Sym('fn'), Cons(Vec((Sym('a'), Sym('b'))), Cons(Cons(Sym('*'), Cons(Sym('a'), Cons(Sym('b'), Nil()))), Nil()))), initial_env)
Fn(params=(Sym(n='a'), Sym(n='b')), body=Cons(hd=Sym(n='*'), tl=Cons(hd=Sym(n='a'), tl=Cons(hd=Sym(n='b'), tl=Nil()))), env={Sym(n='+'): <function <lambda> at 0x1029c1bd0>, Sym(n='-'): <function <lambda> at 0x1029c1ea0>, Sym(n='*'): <function <lambda> at 0x1029c1fc0>, Sym(n='/'): <function <lambda> at 0x1029c2050>, Sym(n='<'): <function <lambda> at 0x1029c20e0>, Sym(n='>'): <function <lambda> at 0x1029c2170>})
```

. . .

```python
>>> # ((fn [a] (* a 11)) 7)  -> 11
>>> eval_expr(Cons(Cons(Sym('fn'), Cons(Vec((Sym('a'),)), Cons(Cons(Sym('*'), Cons(Sym('a'), Cons(11, Nil()))), Nil()))), Cons(7, Nil())), initial_env)
77
```

## How does Pack compare?

* Symbols in Pack are namespaced.
  - `pack.core/+`{.clojure} → `Sym('pack.core', '+')`{.python}
* Symbols resolve to a mutable value cell called a Var
* Pack has 11 special forms, rather than 2
* Persistent, immutable Vector and Map types with _O(log~32~(n))_ access.
* _... blah blah blah_

## Match Case - What does this buy us?

TODO: write an example from the compiler without using match/case
  and compare

## Match Case - Can you spot the bug?

<!-- The first case in the lower match   -->
<!-- Case statements do not fall through -->

```python
def nest_loop_in_recursive_fn(expr):
    def contains_recur(expr):
        ...

    match expr:
        case Cons(Sym(None, 'fn'), Cons(params, Cons(body, Nil()))):
            if contains_recur(body):
                loop = Cons(Sym(None, 'loop'),
                            Cons(Vec.from_iter(untake_pairs(zip(params, params))),
                                 Cons(body, nil)))
                return Cons(Sym(None, 'fn'),
                            Cons(params,
                                 Cons(loop, nil)))
        case other:
            return other
```

## Match Case Pitfalls

* Easy to forget a positional argument when matching dataclasses
  - `case Cons(hd):`{.python} is the same as `case Cons(hd, _)`{.python}
    - so would match `Cons(1, Cons(2, Cons(3, Nil())))`{.python} etc
* Easy to accidentally return None:
  * Have a default case or return an error
  * Start writing the function with a `raise NotImplementedError`{.python} at the bottom
  * Use `typing.NoReturn`{.python} or (new in python 3.11)
    `typing.Never`{.python}
* The ordering of case statements matters
  - Our `case Cons(proc, args)`{.python} must come after our
    `case Cons(Sym('if'), ...):`{.python}


## Match Case Pitfalls

* `[ ]` matches any sequence, not just a list
* Not possible to factor out constants
  - Suppose `FN = Sym('fn')`{.python}
  - `case Cons(FN, _):`{.python} captures the symbol name as FN
    + e.g. `Cons(Sym('if'))`{.python}
      would match and give `FN`{.python} bound as `Sym('if')`{.python}
  - `class Forms: FN = Sym('fn')`{.python}
  - `case Cons(Forms.FN, _):`{.python} is now equivalent to
    `case Cons(Sym('fn'), _):`{.python} but is longer 😩

<!--
Failover cases look nice, but lead to errors

Later Dan: what did I mean by this?
-->


## The Itch


<pre><code>
def eval_expr(form, env):
    match form:
        ...
        case Cons(Sym('if'), Cons(predicate, Cons(consequent, Cons(alternative, Nil())))):
            if <mark>eval_expr</mark>(predicate, env):
                return <mark>eval_expr</mark>(consequent, env)
            return <mark>eval_expr</mark>(alternative, env)

        case Cons(procedure_form, argument_forms):
            procedure = <mark>eval_expr</mark>(procedure_form, env)
            args = [<mark>eval_expr</mark>(arg, env) for arg in argument_forms]
            return procedure(*args)
        ...
</pre></code>


## Pack's Interpreter and Compiler Pipeline

:::::::::::::: {.columns}
::: {.column width="33%"}
### Interpreter
- read forms
- expand quasi-quotes
- expand macros
- validate special form syntax
- create defs
- evaluate top level forms
- evaluate expressions
:::
::: {.column width="33%"}
### Compiler
- extract closure
- deduce scope
- replace complex quoted data
- replace data literals
- hoist lambdas
- resolve qualified symbols
:::
::: {.column width="33%"}
- nest loop within recursive fn
- replace loop/recur with while-true
- convert to intermediate
- convert `if` expression -> statement
- hoist statements
- place return
- convert to python
:::
::::::::::::::

##

How do we avoid repetition and mistakes?

::: notes
Doing something similar to that evaluator for all 19 syntactical passes
is likely to be very error prone.
:::

## Recursion Schemes

Idea:

Can we just write the recursion once?

## `fmap`

Answer: yes

```python
def fmap(f, form):
    match form:
        case Cons(Sym('fn'), Cons(Vec() as params, Cons(body, Nil()))):
            return Cons(Sym('fn'), Cons(Vec() as params, Cons(f(body), Nil())))

        case Cons(Sym('if'), Cons(predicate, Cons(consequent, Cons(alternative, Nil())))):
            return Cons(Sym('if'), Cons(f(predicate), Cons(f(consequent), Cons(f(alternative), Nil()))))

        case Cons(procedure_form, argument_forms):
            return Cons(f(procedure_form), to_cons_list(map(f, [*argument_forms])))

        case other:
            return other
```


##

rewriting to use a single pass

```python
def convert_if_expr_to_stmt(i=0):

    fst = lambda pair: pair[0]
    snd = lambda pair: pair[1]

    def alg(expr):
        """
        ExprF[(ExprF, contains_stmt: Bool)] -> (ExprF, contains_stmt: Bool)
        """
        match expr:
            # c1 and c2 are whether those arms of the if expression
            # contain any statements - as calculated in the default
            # case
            case IfExpr((pred, _), (con, c1), (alt, c2)) if c1 or c2:
                t = next_temp()
                # statement hoisting will clean this up
                return Do((
                    IfStmt(pred,
                           con if is_stmt(con) else SetBang(t, con),
                           alt if is_stmt(alt) else SetBang(t, alt)),
                ), t), True
            case other:
                contains = reduce_ir(False, operator.or_, fmap_ir(snd, other))
                return (fmap_ir(fst, other), contains or is_stmt(other))
        assert False
    return alg
```

then realise we can use zygomorphism to remove most of this
base case


## Future Work / Ideas

- ~~Finish compilation (i.e. transpilation) pipeline~~
- python keyword argument compatibility
- Add `try` `except`
- Try to return to a regular sleeping pattern

## Recursion Schemes - Resources

### Useful resources

- <https://github.com/sellout/recursion-scheme-talk>
- <https://github.com/precog/matryoshka>


## Source Code

### Pack Itself

- <https://github.com/cakemanny/pack-lang>

### This Talk

- <https://github.com/cakemanny/talks>


## `IndexError: slide index out of range`

## Rejected Material

## Syntax - Symbols

### Symbols

```clojure
    x
    my-variable
    <- ;; symbols are symbols too
    🚪 ;; 😈

   user/my-var
;  ^--^
;    \ namespace

    com.bettermarks.math/+
;      ^
;       \ dots make directories
```

```clojure
user=> (def 🤦 5)
#'user/🤦
user=> 🤦
5
user=> (+ 🤦 5)
10
```



## Data Structures

More than just lists!

- Lists `(a b c)`
- Vectors `[a b c]`
- Maps i.e. dictionaries `{:a b :c d}`

All are immutable


## Data Structures - Lists

```clojure
'(1 "one" 'two)
```

![_the structure of a list_](lists.svg)


## Data Structures - Lists
### Implementation

The cons cell you all know and love.

```python
    @dataclass(frozen=True, slots=True)
    class Cons(List):
        hd: Any
        tl: 'Optional[List]'
        ...
```

Nil: Something to stick at the end. The empty list `()`

```python
    class Nil(List):
        __slots__ = ()
        ...

    nil = Nil()
    # all instances of Nil() are nil
    Nil.__new__ = lambda cls: nil
```

<!-- I wanted to put None there, but then you don't get such a nice repr -->
<!-- None works some of the time though -->


## Data Structures - Lists

In Python that looks like:

```python
Cons(1,
     Cons('one',
          Cons(Sym(None, "two"),
               nil)))
```


## Data Structures - Vectors

```clojure
[a b c 1 2 3]
```

![_a single node vector_](vector1.svg)

![_a vector with 100 elements_](vector2.svg)


## Data Structures - Vectors

```python
@dataclass(frozen=True, slots=True)
class Vec(Sequence):
    xs: tuple[Any | 'Vec']
    height: int

    def __getitem__(self, idx: int):

        if self._is_leaf():
            return self.xs[idx]

        subvec_idx = idx >> (5 * self.height)

        mask = (1 << (5 * self.height)) - 1

        return self.xs[subvec_idx][mask & idx]
    ...
```


## Data Structures - Vectors

Indexing involves splitting up the index (`idx`) into groups of 5 bits
to get the correct offset in each level of the tree

```python
>>> from pack.interp import Vec
>>> v1 = Vec.from_iter(range(100))
>>> bin(70)
'0b1000110'
```

```
     00010 00110
        \     \ Index for height 0
         Index for height 1
```

```python
>>> v1.xs[0b10].xs[0b00110]
70
>>> v1[70]
70
```


## Data Structures - Maps


![_A HAMT_](maps.svg){ width=90% }



## Data Structures - Maps


![_A HAMT_](maps.svg){ width=50% }

```
_hash32(:these)  = 3487490880 = 00000 00011 00111 11101 11101 11000 11010 00000
_hash32(:are)    = 1726257865 = 00000 00001 10011 01110 01001 00110 10110 01001
_hash32(:they)   = 3908472888 = 00000 00011 10100 01111 01101 00100 00001 11000
_hash32(:rather) =  843060011 = 00000 00000 11001 00100 00000 00100 11001 01011
                                          ^
                                           \
```

Here we see where `:these` and `:they` have clashed in group 6, and so
get pushed down into a level 5 node

_and writing this slide I notice the bug... we should be starting height from 6_

<!-- TODO: add another bitset to indicate which slots are empty  -->

<!--
##

Sometimes data structures are hard... 🤦

```
(Pdb) p entry[1]
[y 2]
(Pdb) p v
[]
(Pdb) p entry[1] == v
True
(Pdb)
```
-->

## Namespaces ?

```clojure
(ns my-namespace-name)
```

```clojure
```


