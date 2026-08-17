> Agent-side expertise file — **not user-facing tour material**.
> Canonical source (READ-ONLY, never edit there):
> `/home/x/Documents/obso-site/pidp1-sw/lisp1_5.md`. Copied 2026-08-17.

# IBM 7090 LISP 1.5 Programming Guide

## Historical Context and Overview

**LISP 1.5** was developed at MIT in 1962 by John McCarthy, Paul W. Abrahams, Daniel J. Edwards, Timothy P. Hart, and Michael I. Levin. This implementation for the IBM 7090 computer represents one of the most influential early programming languages, establishing foundational concepts that persist in modern computing.

### Revolutionary Characteristics

1. **Symbolic Expressions (S-expressions)**: All data represented as symbolic expressions with indefinite length and branching tree structure
2. **Dynamic Memory Management**: List structures with automatic garbage collection freed programmers from manual memory allocation
3. **Self-Modifying Code**: LISP could interpret and execute programs written as S-expressions, enabling meta-programming

## Core Language Architecture

### S-expressions (Data Language)

**Atomic Symbols:**
- Strings of up to 30 numerals and capital letters
- First character must be a letter
- Examples: `A`, `APPLE`, `PART2`, `EXTRALONGSTRINGOFLETTERS`, `A4B66XYZ2`

**Dot Notation (Fundamental Syntax):**
```lisp
; Basic S-expression combines two expressions
(A . B)

; Recursive structure
((A . B) . C)
((U . V) . (X . Y))
(A . (B . (C . NIL)))
```

**List Notation (Convenience Syntax):**
```lisp
; List notation equivalents
(A B C) ≡ (A . (B . (C . NIL)))
((A B) C) ≡ ((A . (B . NIL)) . (C . NIL))
(A B (C D)) ≡ (A . (B . ((C . (D . NIL)) . NIL)))
(A) ≡ (A . NIL)
() ≡ NIL
```

### M-expressions (Meta-language)

**Function Definition Syntax:**
- Function names: lowercase letters
- Arguments: `function[arg1; arg2; ...]`
- Composition: nested brackets allowed

**Conditional Expressions:**
```lisp
[p1→e1; p2→e2; ...; pn→en]
```
- Evaluates predicates `pi` left to right until one is true
- Returns corresponding expression `ei`
- `T` represents always-true condition

**Lambda Notation:**
```lisp
λ[[x1; x2; ...]; expression]
```
- Binds variables in expression
- Essential for function definition
- Variables are dummy/bound variables

**Label Notation:**
```lisp
label[name; λ-expression]
```
- Enables recursive function definition
- Binds function name within its own definition

## Built-in Functions

### Elementary Functions

**Core List Operations:**
```lisp
car[x]        ; Returns first part of composite expression
cdr[x]        ; Returns second part of composite expression
cons[x; y]    ; Creates new S-expression (x . y)

; Examples
car[(A . B)] = A
cdr[(A . B)] = B
cons[A; B] = (A . B)
car[cons[x; y]] = x
cdr[cons[x; y]] = y
```

**Predicates:**
```lisp
atom[x]       ; True if x is atomic symbol
eq[x; y]      ; True if x and y are identical atomic symbols
null[x]       ; True if x is NIL
equal[x; y]   ; True if x and y are identical S-expressions (recursive)

; Examples
atom[A] = T
atom[(A . B)] = F
eq[A; A] = T
eq[A; B] = F
null[NIL] = T
null[()] = T
```

### List Processing Functions

**List Manipulation:**
```lisp
append[x; y]    ; Concatenates lists (copies first list)
reverse[x]      ; Reverses top level of list
member[x; y]    ; True if x is member of list y
length[x]       ; Returns number of elements in list
copy[x]         ; Creates complete copy of list structure

; Examples
append[(A B); (C D)] = (A B C D)
reverse[(A B C)] = (C B A)
member[B; (A B C)] = T
length[(A B C)] = 3
```

**Advanced List Operations:**
```lisp
subst[x; y; z]     ; Substitutes x for all occurrences of y in z
sublis[alist; expr] ; Multiple substitutions using association list

; Examples
subst[X; A; (A B A)] = (X B X)
sublis[((A . X) (B . Y)); (A B C)] = (X Y C)
```

### Association Lists and Property Lists

**Association List Functions:**
```lisp
pair[x; y]        ; Creates list of pairs from two lists
sassoc[x; y; u]   ; Searches association list for key x
get[x; y]         ; Retrieves property y from property list of x

; Examples
pair[(A B); (1 2)] = ((A . 1) (B . 2))
sassoc[A; ((A . 1) (B . 2)); NIL] = 1
```

### Arithmetic Functions

**Basic Arithmetic:**
```lisp
plus[x1; ...; xn]     ; Sum of arguments
difference[x; y]      ; x minus y
times[x1; ...; xn]    ; Product of arguments
quotient[x; y]        ; Integer quotient
remainder[x; y]       ; Remainder of division
expt[x; y]           ; x to the power y
minus[x]             ; Arithmetic negation

; Examples
plus[1; 2; 3] = 6
difference[5; 3] = 2
times[2; 3; 4] = 24
quotient[7; 3] = 2
remainder[7; 3] = 1
```

**Arithmetic Predicates:**
```lisp
lessp[x; y]      ; x < y
greaterp[x; y]   ; x > y
zerop[x]         ; x = 0
onep[x]          ; x = 1
minusp[x]        ; x < 0
numberp[x]       ; x is a number
fixp[x]          ; x is fixed-point number
floatp[x]        ; x is floating-point number
```

**Logical Operations (on 36-bit words):**
```lisp
logor[x1; ...; xn]    ; Bitwise OR
logand[x1; ...; xn]   ; Bitwise AND
logxor[x1; ...; xn]   ; Bitwise exclusive OR
leftshift[x; n]       ; Bit shifting
```

### Higher-Order Functions

**Functional Arguments:**
```lisp
maplist[x; fn]     ; Applies function to successive sublists
mapcon[x; fn]      ; Like maplist but concatenates results
map[x; fn]         ; Like maplist but used for side effects only
search[x; p; f; u] ; Searches list with predicate

; Examples
maplist[(A B C); car] = (A B C)
mapcon[(A B C); list] = ((A) (B) (C))
```

### Logical Connectives

```lisp
and[x1; x2; ...; xn]  ; Evaluates left to right, stops at first false
or[x1; x2; ...; xn]   ; Evaluates left to right, stops at first true
not[x]                ; Logical negation
```

## Special Forms

### QUOTE
```lisp
(QUOTE expr)    ; Prevents evaluation of its argument
'expr           ; Alternative syntax (in some contexts)

; Examples
(QUOTE A) = A
(QUOTE (A B C)) = (A B C)
```

### COND
```lisp
(COND (p1 e1) (p2 e2) ... (pn en))
; Conditional evaluation with multiple branches
; First true predicate determines result

; Example
(COND ((ATOM X) X)
      ((EQ (CAR X) (QUOTE A)) (QUOTE FOUND-A))
      (T (QUOTE NOT-FOUND)))
```

### LAMBDA
```lisp
(LAMBDA (var1 var2 ...) body)
; Creates anonymous functions
; Essential for functional arguments

; Example
(LAMBDA (X Y) (CONS X Y))
```

### LABEL
```lisp
(LABEL name lambda-expr)
; Enables recursive function definition
; Binds function name within its own body

; Example
(LABEL FF (LAMBDA (X) (COND ((ATOM X) X)
                            (T (FF (CAR X))))))
```

### FUNCTION
```lisp
(FUNCTION expr)
; Used for functional arguments
; Similar to QUOTE but for functions

; Example
(MAPLIST '(A B C) (FUNCTION CAR))
```

## Evaluation Model

### The Universal Function

**evalquote[fn; args]** - The foundation of LISP 1.5 evaluation:
```lisp
evalquote[fn; args] = [get[fn; FEXPR] ∨ get[fn; FSUBR] → eval[cons[fn; args]; NIL];
                      T → apply[fn; args; NIL]]
```

**Core Evaluation Functions:**

**apply[fn; x; a]:**
- Handles function application with association list `a`
- Processes different function types:
  - Elementary functions (CAR, CDR, CONS, ATOM, EQ)
  - LAMBDA expressions (binds variables)
  - LABEL expressions (recursive functions)
  - SUBR (machine language subroutines)

**eval[e; a]:**
- Evaluates forms with association list `a`
- Handles:
  - Atomic symbols (variables) - looked up in association list
  - QUOTE forms - returns literal value
  - COND forms - conditional evaluation
  - Function applications

### Function Types

**EXPR**: LISP-defined functions with evaluated arguments
**FEXPR**: LISP-defined special forms with unevaluated arguments
**SUBR**: Machine language functions with evaluated arguments
**FSUBR**: Machine language special forms with unevaluated arguments

### Property Lists

Every atomic symbol has an associated property list containing:
- **PNAME**: Print name representation
- **EXPR**: Function definition (for LISP functions)
- **SUBR**: Machine language function pointer
- **APVAL**: Permanent value (for constants)
- **FEXPR**: Special form definition
- **FSUBR**: Machine language special form

## Programming Model

### Variable Binding

**Dynamic Scoping:**
- Variables bound through lambda expressions
- Association lists (a-lists) track variable bindings
- Most recent binding visible throughout execution

**Constants:**
```lisp
; Created via property lists with APVAL indicator
; Self-evaluating: NIL, T, numbers
```

### Function Definition

**Using define pseudo-function:**
```lisp
; Example function definition
define[ff; lambda[x; cond[atom[x] → x; T → ff[car[x]]]]]
```

**Manual property list manipulation:**
```lisp
; Direct property list assignment
rplacd[get[FACTORIAL; EXPR];
       lambda[n; cond[zerop[n] → 1; T → times[n; factorial[difference[n; 1]]]]]]
```

### PROG Feature (Imperative Programming)

```lisp
(PROG (var-list)
  label1 (statement1)
  label2 (statement2)
  (GO label1)
  (RETURN value))
```

**Key Features:**
- Program variables initialized to NIL
- `SETQ` for assignment
- `GO` for transfers (only on top level or in COND)
- `RETURN` for function exit

**Example:**
```lisp
length[l] = prog[[u; v];
             v := 0;
             u := l;
        A    [null[u] → return[v]];
             u := cdr[u];
             v := add1[v];
             go[A]]
```

## Data Types and Representation

### Numbers

**Fixed-Point Numbers:**
- Integers with optional sign
- Examples: `-17`, `32719`, `0`

**Floating-Point Numbers:**
- Decimal point required (not first/last character)
- Optional exponent: `6.E1`, `600.00E-1`, `0.6E+2`
- 8 decimal digits precision
- Range: 2^-128 to 2^128

**Octal Numbers:**
- Format: digits followed by 'Q'
- Optional scale factor: `777Q4`, `-7Q11`
- Used for logical operations

### Character Handling

**BCD Encoding:**
- 6-bit characters, 48 legal punch characters
- Functions: `pack`, `unpack`, `mknam`
- Character classification predicates

## Input/Output System

### Basic I/O Functions

```lisp
read[]        ; Reads one S-expression from input
print[x]      ; Prints S-expression to output
punch[x]      ; Outputs to card punch
prin1[x]      ; Prints atomic symbol without newline
terpri[]      ; Terminates print line
```

### System Integration

**Job Control:**
- Overlord monitor system controlled execution
- TEST/SET packets for program organization
- Automatic core memory management

**Memory Layout (IBM 7090 specific):**
- Different system components at specific addresses
- Tape drives: SYSTAP, SYSTMP, SYSPIT, SYSPOT, SYSPPT
- Free storage allocation and garbage collection

## Programming Patterns and Examples

### Recursive List Processing

**Basic Pattern:**
```lisp
function[x] = [atom[x] → base-case;
               T → combine[process[car[x]]; function[cdr[x]]]]
```

**Example - First Atomic Symbol:**
```lisp
ff[x] = [atom[x] → x; T → ff[car[x]]]

; Evaluation trace:
ff[((A . B) . C)]
= ff[car[((A . B) . C)]]
= ff[(A . B)]
= ff[car[(A . B)]]
= ff[A]
= A
```

### Mathematical Computations

**Absolute Value:**
```lisp
abs[x] = [minusp[x] → minus[x]; T → x]
```

**Factorial:**
```lisp
factorial[n] = [zerop[n] → 1; T → times[n; factorial[difference[n; 1]]]]
```

**Greatest Common Divisor (Euclidean Algorithm):**
```lisp
gcd[x; y] = [greaterp[x; y] → gcd[y; x];
             zerop[remainder[y; x]] → x;
             T → gcd[remainder[y; x]; x]]
```

### Association List Processing

**Table Lookup:**
```lisp
lookup[key; table] = [null[table] → NIL;
                      eq[key; caar[table]] → cdar[table];
                      T → lookup[key; cdr[table]]]
```

**Symbol Table Operations:**
```lisp
; Add binding to association list
bind[var; val; alist] = cons[cons[var; val]; alist]

; Update existing binding
update[var; val; alist] = [null[alist] → NIL;
                           eq[var; caar[alist]] → cons[cons[var; val]; cdr[alist]];
                           T → cons[car[alist]; update[var; val; cdr[alist]]]]
```

### Functional Programming Patterns

**Higher-Order Function Usage:**
```lisp
; Apply function to all elements
change[a] = maplist[a; lambda[j; cons[car[j]; X]]]

; Filter list elements
filter[pred; lst] = [null[lst] → NIL;
                     pred[car[lst]] → cons[car[lst]; filter[pred; cdr[lst]]];
                     T → filter[pred; cdr[lst]]]
```

### Conditional Logic Patterns

**Multiple Comparisons:**
```lisp
classify[x] = [atom[x] → (QUOTE ATOM);
               null[x] → (QUOTE EMPTY);
               eq[length[x]; 1] → (QUOTE SINGLETON);
               T → (QUOTE LIST)]
```

## System Features

### Debugging and Development

**Trace Facility:**
```lisp
trace[fn1; fn2; ...]    ; Monitor function entry/exit
untrace[fn1; fn2; ...]  ; Remove tracing
```

**Error Handling:**
```lisp
errorset[expr; flag]    ; Graceful error recovery
```

### Compiler System

**Features:**
- Translates S-expressions to machine code
- 10-100x speed improvement over interpreter
- Self-bootstrapping capability
- Special variable declarations (SPECIAL, COMMON)

### Memory Management

**Garbage Collection:**
- Automatic when memory exhausted
- Uses sign bits for marking in free storage
- Bit tables for full-word space marking
- Reclaims unreachable list structures

**Free Storage:**
- `cons` allocates from free-storage list
- Garbage collector rebuilds free list when exhausted
- Property lists and list structures share memory pool

## Key Differences from Modern Lisp

### Architectural Differences

1. **Scoping**: Dynamic scoping only (no lexical closures)
2. **Namespaces**: Functions and variables share namespace
3. **Memory**: Manual list structure awareness required
4. **Types**: Limited type system (atoms, numbers, lists only)

### Language Features

1. **Control Flow**: PROG feature for imperative style
2. **Function Types**: Clear EXPR/FEXPR/SUBR/FSUBR distinction
3. **Property Lists**: Metadata storage for every atom
4. **No Macros**: Limited syntactic extensibility

### Programming Paradigm

1. **Pure Functional Core**: With imperative extensions via PROG
2. **Interactive Development**: Batch processing model primarily
3. **Meta-Programming**: Full support for code as data

## Historical Significance

LISP 1.5 established foundational concepts that remain central to modern computing:

- **Garbage Collection**: Automatic memory management
- **Dynamic Typing**: Runtime type checking
- **Functional Programming**: Functions as first-class objects
- **Meta-Programming**: Code as data manipulation
- **Symbolic Computation**: Non-numeric data processing
- **Interactive Development**: Read-eval-print loops

This implementation demonstrated that high-level symbolic computation was practical on real hardware, influencing decades of programming language development and artificial intelligence research.

## Practical Programming Considerations

### Memory Efficiency
- Be conscious of `cons` operations (each consumes memory)
- Understand garbage collection timing
- Share common subexpressions when possible

### Function Definition Strategy
- Prefer pure functions for clarity and debugging
- Use PROG for performance-critical iterations
- Leverage property lists for metadata storage

### Debugging Techniques
- Use trace facility for function monitoring
- Employ errorset for graceful error handling
- Structure conditionals for clear logic flow

LISP 1.5 represents a remarkable achievement in programming language design, demonstrating mathematical elegance combined with practical utility that enabled groundbreaking work in artificial intelligence and symbolic computation.