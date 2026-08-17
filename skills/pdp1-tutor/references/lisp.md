> Agent-side expertise file — **not user-facing tour material**.
> Canonical source (READ-ONLY, never edit there):
> `/home/x/Documents/obso-site/pidp1-sw/lisp.md`. Copied 2026-08-17.

# PDP-1 Lisp Programming Language

This document summarizes the PDP-1 Lisp implementation from the 1964 DECUS document by L. Peter Deutsch and Edmund C. Berkeley. This is one of the earliest Lisp implementations, created for the Digital Equipment Corporation PDP-1 computer.

## Historical Context

- **Date**: March 1964
- **Authors**: L. Peter Deutsch and Edmund C. Berkeley
- **Hardware**: PDP-1 computer (18-bit words, 4K-16K memory)
- **Significance**: Early implementation of LISP outside of IBM 7090 systems

## System Requirements

- **Minimum**: 2000 (decimal) registers out of 4096 in one-core PDP-1
- **Maximum**: 16,361 registers in four-core PDP-1
- **Memory organization**: 18-bit words, octal addressing (0000-7777)
- **Number system**: 1's complement arithmetic, octal by default

## Basic Functions

### A. Functions Identical to IBM 7090 LISP

```lisp
ATOM        ; Test if argument is atomic
CAR         ; Return first element of list
CDR         ; Return rest of list
COND        ; Conditional expression
CONS        ; Construct list cell
EVAL        ; Evaluate expression
GENSYM      ; Generate unique symbol
GO          ; Transfer control in PROG
LIST        ; Create list from arguments
LOGAND      ; Logical AND
LOGOR       ; Logical OR
MINUS       ; Arithmetic negation
NULL        ; Test for NIL
NUMBERP     ; Test if argument is numeric
PLUS        ; Arithmetic addition
PRINT       ; Print expression
PROG        ; Program feature for iteration
QUOTE       ; Prevent evaluation
READ        ; Read S-expression
RETURN      ; Return from PROG
RPLACA      ; Replace CAR of list
RPLACD      ; Replace CDR of list
SASSOC      ; Search association list
SETQ        ; Set variable value
TERPRI      ; Print carriage return
```

### B. Functions Different from 7090 LISP

```lisp
EQ          ; Works on both atoms and numbers (not just atoms)
GREATERP    ; Tests X > Y (not X ≥ Y as in 7090)
STOP        ; Equivalent to PAUSE, takes numerical argument
PRIN1       ; Prints atom without extra space, returns NIL
```

### C. Functions Unique to PDP-1

```lisp
XEQ         ; Execute machine language instructions
            ; (XEQ C A I) executes instruction C with A in accumulator,
            ; I in I/O register, returns (a i p) where p is skip flag

LOC         ; Returns machine register where atom/list begins
            ; (LOC X) gives memory location of X
```

## Special Forms and Objects

### Special Form
```lisp
LAMBDA      ; Function definition (identical to 7090 LISP)
```

### Permanent Objects
```lisp
OBLIST      ; Current list of atomic symbols
NIL         ; Empty list / false value (replaces F from 7090)
T           ; True value
EXPR        ; Expression type indicator
SUBR        ; Subroutine type indicator
FEXPR       ; Special form indicator
FSUBR       ; Function subroutine indicator
APVAL       ; Atomic value indicator
```

## Data Types and Representation

### Numbers
- **Default base**: Octal (10 = 8 decimal, 100 = 64 decimal)
- **Arithmetic**: 1's complement (777777 = -0, 777776 = -1)
- **Range**: 18-bit signed integers
- **No floating point**: All arithmetic is integer-based

### Atoms and Lists
- **Character encoding**: 6-bit "concise code"
- **Packing**: 3 characters per 18-bit word
- **Print names**: Not part of property lists
- **Symbol length**: Effectively unlimited
- **Memory structure**: Linked list representation

## Input/Output System

### Character I/O (Typewriter)
```lisp
TYO         ; Type out character from I/O register
TYI         ; Type in character, sets Program Flag 1
```

**Critical TYI Programming Pattern:**
```assembly
inloop, cla         ; Clear accumulator
        cli         ; Clear IO register
        szf 1       ; Skip if program flag 1 is SET
        jmp inloop  ; Flag clear, keep waiting
        tyi         ; Flag set, read character (clears flag 1)
        ; Character now in IO register bits 12-17
```

### Paper Tape I/O
```lisp
RPA         ; Read Perforated Tape Alphanumeric (8-bit)
RPB         ; Read Perforated Tape Binary (18-bit)
PPA         ; Punch Perforated Tape Alphanumeric
PPB         ; Punch Perforated Tape Binary
```

### CRT Display
```lisp
DPY         ; Display point: AC bits 0-9 = X, IO bits 0-9 = Y
            ; Intensity in instruction bits 9-11 (1's complement)
            ; 3 = brightest, 0 = normal, 7 = barely visible
```

## Input Format and Syntax

### S-Expression Input
- **Termination**: Extra space required after final parenthesis
- **Equivalences**: Tab, space, and comma are equivalent
- **Case**: Upper and lower case noted but stored as lowercase
- **Backspace**: Deletes to last control character
- **Character escapes**: Overbar `¯` or vertical bar `|` makes next character literal

**IMPORTANT NOTE ON CASE:** Basic functions (such as CAR, CDR) are actually stored as lower-case symbols (such as car, cdr) and are input and output by the system as lower-case symbols. While this manual shows uppercase examples for clarity, all actual programming should use lowercase for consistency with the system's internal representation.

### Number Input
- **Default**: Octal integers
- **Negative numbers**: Must use octal representation (e.g., 777776 for -1)
- **Switching bases**: Use `DECIMAL` and `OCTAL` pseudo-instructions

### Function Evaluation
Unlike IBM 7090 LISP, arguments are evaluated at top level:
```lisp
; To evaluate cons [A;B], you must write:
(CONS (QUOTE A) (QUOTE B))
```

## Programming Patterns

### Basic Evaluation
```lisp
(CAR (QUOTE (A B C D)))     ; Returns A
(CDR (QUOTE (A B C D)))     ; Returns (B C D)
(LIST (QUOTE (A B C D)))    ; Returns ((A B C D))
```

### Conditional Logic
```lisp
(COND ((EQ T NIL) (STOP 1))
      (T (EQ (PLUS 1 1) 2)))
```

### Program Feature (Iteration)
```lisp
(PROG (U)
  (PRINT NIL)
  (TERPRI)
  (PRINT T)
  (SETQ U T)
  (RETURN U))
```

### Function Definition
```lisp
(RPLACD (QUOTE CAAR) (QUOTE
  (EXPR (LAMBDA (X) (CAR (CAR X))))))
```

## Auxiliary Functions (Can be Defined)

The document provides LISP definitions for additional functions:

### List Processing
```lisp
APPEND      ; Concatenate lists
REVERSE     ; Reverse list order
SUBLIS      ; Substitute throughout list
SUBST       ; Substitute in list
MEMBER      ; Test list membership
LENGTH      ; Count list elements
```

### Arithmetic Extensions
```lisp
TIMES       ; Multiplication using recursion
DIFFERENCE  ; Subtraction
QUOTIENT    ; Division
REMAINDER   ; Division remainder
ZEROP       ; Test for zero
```

### Logical Extensions
```lisp
GREATERP    ; Comparison predicate
SMALLER     ; Comparison predicate
UNION       ; Set union
```

## System Management Functions

### Memory Management
```lisp
XSY         ; Expunge symbols from OBLIST
REMOVE      ; Remove specific symbols from OBLIST
```

**Example usage:**
```lisp
(REMOVE OBLITT F Y)  ; Removes F, OBLITT, Y from OBLIST
```

### Machine Language Integration
```lisp
DEPOSIT     ; Store list of numbers starting at address
PUTSUBR     ; Define machine language subroutine
DEFSUBR     ; Name existing machine routine
```

**Example:**
```lisp
(PUTSUBR (QUOTE SHOWLINE) (LIST 345507 445507 205507 730007
         640400 605501 602241) 5500)
```

## Error Diagnostics

### Error Codes
- **icd** - Illegal COND; returns NIL and continues
- **uss** - Unbound symbol in SETQ; returns NIL and continues
- **tma** - Too many arguments for SUBR; ignores extras
- **uas** - Unbound atomic symbol (followed by form being evaluated)
- **ilp** - Illegal parity; halts with character in accumulator
- **lts** - LAMBDA variable list too short
- **ats** - Argument list too short
- **sce** - Storage capacity exceeded
- **pce** - Pushdown capacity exceeded
- **nna** - Non-numeric argument for arithmetic
- **ana** - Argument not atom (for PRIN1)
- **ovf** - Division overflow

### Recovery
Most errors allow continuation with CONTINUE button. Storage capacity errors require deleting symbols from OBLIST.

## Hardware Interface

### Sense Switches
- **SS 1** - Idiot trace
- **SS 3** - Punch out
- **SS 5** - Type in control
- **SS 6** - No typeout

### Program Flags
- **PF 1** - Used for type-in (automatically set/cleared)
- **PF 2** - Zero suppress in octal print
- **PF 5** - Letter in symbol
- **PF 6** - Off in error printout

### Console Operations
- **EXAMINE** - Display memory contents
- **DEPOSIT** - Store value in memory
- **SINGLE STEP** - Execute one instruction
- **START** - Begin execution
- **CONTINUE** - Resume execution

## System Operation

### Loading and Starting
1. Zero core memory (not necessary at all)
2. Load binary tape with READIN
3. Machine halts at address 4
4. Set storage parameters in Test Word switches if desired
5. Set push-down list length in Test Word switches
6. Turn up Sense Switch 5 for typewriter control
7. Press CONTINUE to start READ-EVAL-PRINT loop

### Memory Layout
- **7751-7777** - Read-in routine (23 registers reserved)

### Integration with Other Software
- **DDT compatibility** - Can load Digital Debugging Tape above 5500
- **Machine subroutines** - Can be located above LISP storage
- **Core dump routines** - Can be loaded in 400 registers above storage

## Key Differences from Modern Lisp

1. **Memory constraints** - Very limited memory requires careful management
2. **No floating point** - Only integer arithmetic available
3. **Octal default** - All numbers are octal unless explicitly decimal
4. **Hardware integration** - Direct access to machine registers and I/O
5. **Manual memory management** - Explicit garbage collection control
6. **Character limitations** - 6-bit character set, case handling issues
7. **Interactive debugging** - Hardware-level debugging features
8. **Paper tape I/O** - Persistent storage via perforated tape
9. **Real-time constraints** - Timing considerations for I/O operations
10. **Assembly integration** - Seamless calling of machine language routines

## Programming Best Practices

1. **Use PROG to avoid recursion** where possible to save stack space
2. **Be careful with symbol names** - 6 character limit can cause conflicts
3. **Manage OBLIST** - Remove unused symbols to free memory
4. **Use XSY and REMOVE** for memory cleanup
5. **Test with sense switches** for program control
6. **Use machine language** for performance-critical operations
7. **Plan memory layout** carefully to avoid conflicts
8. **Use proper I/O synchronization** especially for typewriter input

This PDP-1 Lisp implementation represents a remarkable achievement in early computer science, providing a functional symbolic processing environment on severely constrained hardware while maintaining the essential character of Lisp programming.





# PDP-1 Lisp: Additional Learnings and Corrections

This document contains important corrections and additional learnings about PDP-1 Lisp discovered after creating the initial `lisp.md` documentation.

## Critical Correction: Variable Usage in PDP-1 Lisp

### Variables MUST be Declared in PROG Forms

**WRONG (Common Misconception):**
```lisp
(SETQ A 4)  ; This will cause "uss - Unbound symbol in SETQ" error
```

**CORRECT:**
```lisp
(PROG (A B)         ; Variables MUST be declared first
  (SETQ A 4)        ; Now SETQ works
  (SETQ B 4)
  (RETURN (PLUS A B)))
```

### Key Variable Rules in PDP-1 Lisp

1. **No global variables** - Variables can only exist within PROG scope
2. **Declaration required** - All variables must be listed in PROG parameter list
3. **Local scope only** - Variables exist only within their PROG form
4. **SETQ restriction** - SETQ only works on declared PROG variables

This is fundamentally different from modern Lisp where you can create global variables with `setq` at any time.

## How to Add 4 + 4: Complete Examples

### Method 1: Direct Calculation (Simplest)
```lisp
(PLUS 4 4)
```
**Result:** `10` (octal) = 8 decimal

### Method 2: Using Variables in PROG
```lisp
(PROG (A B RESULT)
  (SETQ A 4)
  (SETQ B 4)
  (SETQ RESULT (PLUS A B))
  (RETURN RESULT))
```

### Method 3: Define as Reusable Function
```lisp
(RPLACD (QUOTE ADDEM) (QUOTE
  (EXPR (LAMBDA () (PLUS 4 4)))))
```
Then call:
```lisp
(ADDEM)
```

### Method 4: Parameterized Addition Function
```lisp
(RPLACD (QUOTE ADDNUM) (QUOTE
  (EXPR (LAMBDA (X Y) (PLUS X Y)))))
```
Then call:
```lisp
(ADDNUM 4 4)
```

## Running Programs: Step-by-Step Process

### System Startup
1. **Zero core memory** (to avoid conflicts)
2. **Load binary tape** - Put LISP tape in reader, press READIN
3. **Wait for halt** - Machine stops at address 4
4. **Set typewriter mode** - Turn up Sense Switch 5
5. **Start interpreter** - Press CONTINUE
6. **Ready indication** - Program counter shows 1335 (waiting loop)

### Program Execution
1. **Type expression** - Enter your Lisp code
2. **Critical: Add space** - Must have space after final parenthesis
3. **Automatic evaluation** - System immediately processes input
4. **View result** - System prints answer and waits for next input

### Example Interactive Session
```
(PLUS 4 4)
10

(PROG (X Y)
  (SETQ X 4)
  (SETQ Y 4)
  (RETURN (PLUS X Y)))
10

DECIMAL
(PLUS 4 4)
8

OCTAL
(PLUS 4 4)
10
```

## Input/Output Format Details

### Critical Input Requirements
- **Space termination** - MUST include space after final parenthesis
- **Case handling** - Input stored as lowercase regardless of typing
- **Character equivalence** - Tab, space, comma are equivalent separators
- **Backspace function** - Deletes to last control character (parenthesis, space, etc.)

### Number Base Control
```lisp
OCTAL          ; Switch to octal mode (default)
DECIMAL        ; Switch to decimal mode
```

### Output Format
- **Automatic base** - Numbers display in current base (octal by default)
- **No extra spaces** - Unlike IBM 7090 LISP, no padding around output
- **Carriage returns** - Auto-generated after 100 characters

## Error Handling and Recovery

### Common Errors with Variables
- **uss** - "Unbound symbol in SETQ" - Trying to SETQ undeclared variable
- **uas** - "Unbound atomic symbol" - Reference to undefined symbol

### Recovery Procedures
- **CONTINUE button** - Most errors allow continuation
- **START at 4** - Restart READ-EVAL-PRINT loop
- **Memory management** - Use REMOVE to free symbols if storage full

## Programming Patterns

### Iteration with PROG
```lisp
(PROG (I SUM)
  (SETQ I 1)
  (SETQ SUM 0)
  LOOP
  (SETQ SUM (PLUS SUM I))
  (SETQ I (PLUS I 1))
  (COND ((GREATERP I 10) (RETURN SUM)))
  (GO LOOP))
```

### Conditional Logic
```lisp
(PROG (X RESULT)
  (SETQ X 5)
  (COND ((GREATERP X 4) (SETQ RESULT (QUOTE BIG)))
        (T (SETQ RESULT (QUOTE SMALL))))
  (RETURN RESULT))
```

### Function Definition Pattern
```lisp
(RPLACD (QUOTE FUNCNAME) (QUOTE
  (EXPR (LAMBDA (PARAM1 PARAM2)
    (PROG (LOCAL1 LOCAL2)
      ; Function body using PARAM1, PARAM2, LOCAL1, LOCAL2
      (RETURN RESULT))))))
```

## Memory and Performance Considerations

### Variable Scope Benefits
- **Memory efficiency** - Variables only exist when needed
- **Stack management** - Automatic cleanup when PROG exits
- **No global pollution** - Cannot accidentally create persistent variables

### Programming Recommendations
1. **Minimize PROG depth** - Avoid deep nesting to save pushdown stack
2. **Reuse variable names** - Same names in different PROGs don't conflict
3. **Use RETURN explicitly** - Always specify what PROG should return
4. **Prefer direct computation** - `(PLUS 4 4)` is more efficient than variables

## Comparison with Modern Lisp

| Feature | PDP-1 Lisp | Modern Lisp |
|---------|------------|-------------|
| Global variables | None | `setq`, `defvar`, etc. |
| Local variables | PROG only | `let`, `let*`, `lambda` |
| Variable declaration | Required in PROG | Optional in many contexts |
| Scope rules | PROG-bound only | Lexical + dynamic |
| Memory management | Manual with REMOVE | Automatic garbage collection |

## Historical Context

This restricted variable system reflects:
- **Memory constraints** - 4K-16K words total memory
- **Implementation simplicity** - Easier to implement PROG-scoped variables
- **Performance optimization** - No need to search global symbol tables
- **Safety** - Prevents accidental global variable creation

The PDP-1 Lisp variable system, while restrictive, was actually quite elegant for its time and hardware constraints. It forced disciplined programming while providing sufficient expressive power for symbolic computation.

## Key Takeaways

1. **Always use PROG for variables** - No exceptions
2. **Declare before use** - List all variables in PROG parameter list
3. **Local scope only** - Variables cannot escape their PROG
4. **Simple arithmetic works directly** - `(PLUS 4 4)` needs no variables
5. **Interactive nature** - Immediate evaluation and feedback
6. **Space-terminated input** - Critical for proper parsing

This understanding fundamentally changes how one approaches programming in PDP-1 Lisp compared to modern Lisp dialects.




# PDP-1 Lisp: Practical Programming Learnings

This document captures hands-on learnings about PDP-1 Lisp programming, based on practical experience and manual clarifications.

## Case Sensitivity - Critical Discovery

**From the manual:** "Basic functions (such as CAR, CDR) contrary to the representation throughout this report, are actually stored as lower-case symbols (such as car, cdr); and then taken into the system and put out by the system as lower-case symbols."

### **Key Points:**
- **All programming should use lowercase** for consistency
- **System functions are stored internally as lowercase**
- **Manual examples showing uppercase were just for documentation clarity**
- **Input and output use lowercase**

### **Correct Programming Style:**
```lisp
; Correct (lowercase)
(rplacd (quote hello) (quote
  (expr (lambda ()
    (prog ()
      (print (quote hello))
      (terpri)
      (return t))))))

; Call function
(hello)
```

## Function Definition and Storage

### **How Functions Are Actually Stored:**
Functions are stored using `rplacd` to set the CDR of an atomic symbol:

```lisp
; Define function
(rplacd (quote funcname) (quote
  (expr (lambda (args)
    (prog (variables)
      ; function body
      (return result))))))
```

### **How to List/View Functions:**
```lisp
; View the function definition
(print (cdr (quote funcname)))

; This prints the function body:
; (expr (lambda () (prog () ...)))
```

**NOT** using property lists like LISP 1.5's `GET` function.

## Paper Tape Operations

### **Punching Programs to Paper Tape:**

#### **Basic Procedure:**
1. **Turn UP Sense Switch 3** ("Punch out" mode)
2. **Type your program** (output goes to paper tape punch)
3. **Turn DOWN Sense Switch 3** (back to typewriter)

#### **Verified Working Example:**
```lisp
; Manual test (confirmed working)
; 1. Turn UP SS3
; 2. Type:
(print (quote test))
; 3. Turn DOWN SS3
; Result: Successfully punches to tape
```

### **Saving Existing Functions:**
```Use the lisp-defs.pt paper tape containing the pdef function
Example to save myfunction: 
; 1. Turn UP SS3
; 2. Type: (pdef myfunction) 
; 3. Turn DOWN SS3
; Result: Successfully punches to tape
```

## Proper Terminology

### **What You Have When You Define a Function:**
```lisp
(rplacd (quote tt) (quote (expr (lambda () ...))))
```

**Correct Terms:**
- **tt** is an **atomic symbol** (or "atom")
- **tt** has a **function definition** attached
- **tt** is a **function** (most common usage)

### **Proper Usage:**
- ✅ "Call the function tt" - `(tt)`
- ✅ "Punch the function tt to tape"
- ✅ "Save the function definition to tape"
- ✅ "Load the function from tape"

### **Avoid:**
- ❌ "tt is a program" (too general)
- ❌ "Run the program tt" (single function ≠ program)

## Arithmetic Operations

### **Basic Multiplication:**
```lisp
(times 4 4)
; Returns: 20 (octal) = 16 decimal
```

### **Number Base Handling:**
```lisp
; Default is octal
(times 4 4)    ; Returns 20 (octal)

; Switch to decimal
decimal
(times 4 4)    ; Returns 16 (decimal)

; Switch back
octal
```

### **Important Arithmetic Notes:**
- **Integer arithmetic only** (no floating point)
- **Default base is octal**
- **Use lowercase function names**: `times`, not `TIMES`
- **Multiple arguments supported**: `(times 2 3 4)` = 30 (octal)

## Variable Scope Rules

### **CRITICAL: No Global Variables**
```lisp
; This FAILS:
(setq x 42)  ; ERROR: "uss - Unbound symbol in SETQ"

; Variables MUST be declared in PROG:
(prog (x y)
  (setq x 42)   ; Now works
  (return x))
```

### **Function Parameters:**
```lisp
(rplacd (quote add) (quote
  (expr (lambda (x y)          ; Parameters automatically bound
    (prog (result)             ; Local variables declared here
      (setq result (plus x y))
      (return result))))))
```

## Memory Management Considerations

### **No Garbage Collection:**
- System will eventually "run out of CONS"
- Programs must be short-lived or memory-conscious
- Manual cleanup required:

```lisp
(xsy)                    ; Expunge unused symbols
(remove symbol1 symbol2) ; Remove specific symbols
```

### **Memory-Conscious Programming:**
```lisp
; Prefer PROG over deep recursion
; Avoid excessive CONS operations
; Clean up symbols when done
```

## Input Format Requirements

### **Critical Input Rules:**
- **Must add space after final parenthesis**
- **Tab, space, comma are equivalent separators**
- **Backspace deletes to last control character**

```lisp
; Correct input format:
(hello) ←space required here

; Wrong (will hang):
(hello)←no space
```

## System Control

### **Sense Switches:**
- **SS 1** - Idiot trace
- **SS 3** - Punch out (redirect to paper tape)
- **SS 5** - Type in control (typewriter mode)
- **SS 6** - No typeout

### **Basic System Operation:**
1. Load LISP tape with READIN
2. Machine halts at address 4
3. Turn UP SS5 for typewriter control
4. Press CONTINUE
5. Program counter shows 1335 (ready for input)

## Hardware Integration Features

### **Unique PDP-1 Functions:**
```lisp
xeq             ; Execute machine language instructions
loc             ; Get memory location of symbol
tyi/tyo         ; Character I/O
rpa/rpb/ppa/ppb ; Paper tape I/O
dpy             ; CRT display
```

## Programming Best Practices

### **Function Definition Pattern:**
```lisp
(rplacd (quote funcname) (quote
  (expr (lambda (params)
    (prog (locals)
      ; function body using params and locals
      (return result))))))
```

### **Memory Management:**
- Use `prog` to limit variable scope
- Clean up with `xsy` and `remove`
- Avoid deep recursion
- Be conscious of CONS operations

### **Debugging Approach:**
- Use `print` statements liberally
- Test functions incrementally
- Use sense switches for program control
- Leverage hardware debugging (examine/deposit, single step)

## Common Mistakes to Avoid

1. **Using uppercase** when lowercase is expected
2. **Forgetting space after parentheses** in input
3. **Trying to use global variables** outside PROG
4. **Using `(print (cdr (quote func)))` to save** (missing rplacd wrapper)
5. **Assuming decimal arithmetic** when system defaults to octal
6. **Deep recursion** without considering memory limits

This represents practical, hands-on knowledge of PDP-1 Lisp programming based on actual usage and manual clarifications.



# LISP Implementation Differences: IBM 7090 LISP 1.5 vs PDP-1 Lisp

## Historical Context

**IBM 7090 LISP 1.5 (1962)**
- Developed at MIT by John McCarthy's team
- Target: IBM 7090 with 32K 36-bit words
- Full-featured research system
- Foundation for modern Lisp dialects

**PDP-1 Lisp (1964)**
- Created by L. Peter Deutsch and Edmund C. Berkeley
- Target: PDP-1 with 4K 18-bit words (severe constraints)
- Described as a "junior edition" following the LISP 1.5 manual closely
- Strategic subset selection due to memory limitations

## Hardware Constraints Comparison

| Feature | IBM 7090 LISP 1.5 | PDP-1 Lisp |
|---------|-------------------|-------------|
| **Memory** | 32K × 36-bit words | 4K × 18-bit words |
| **Storage** | ~1.1 MB equivalent | ~9 KB equivalent |
| **Arithmetic** | 36-bit 2's complement | 18-bit 1's complement |
| **Number Base** | Decimal default | Octal default |
| **I/O** | Sophisticated tape/card | TTY, paper tape, basic CRT |

## Core Language Features

### ✅ What Both Systems Include (The "Lisp Universal Machine")

**Essential Primitives:**
```lisp
; Core list operations (identical in both)
CAR         ; First element of list
CDR         ; Rest of list
CONS        ; Construct pairs
ATOM        ; Test if atomic
EQ          ; Test equality
NULL        ; Test for NIL

; Evaluation mechanism
EVAL        ; Interpret S-expressions
QUOTE       ; Prevent evaluation
COND        ; Conditional branching

; Function definition
LAMBDA      ; Anonymous functions
LABEL       ; Named recursive functions (in 1.5 via LABEL, in PDP-1 via function definition)
```

**Fundamental Capabilities:**
- S-expression representation (atoms and lists)
- Recursive function evaluation
- Association lists for variable bindings
- Symbol table with interned atoms
- Basic arithmetic (integers only in PDP-1)

### ❌ Major Features Cut from PDP-1 Lisp

#### 1. Garbage Collection
**LISP 1.5:**
```lisp
; Automatic garbage collection with mark-and-sweep
; Programs could run indefinitely
; No programmer intervention needed
```

**PDP-1 Lisp:**
```lisp
; NO garbage collection
; System eventually "runs out of CONS"
; Programs must be short-lived or very careful
; Manual memory management via REMOVE/XSY
```

#### 2. Floating-Point Arithmetic
**LISP 1.5:**
```lisp
; Full numeric tower
6.E1            ; Floating point numbers
0.6E+2          ; Scientific notation
600.00E-1       ; Various formats
(PLUS 3.14 2.0) ; Mixed arithmetic
```

**PDP-1 Lisp:**
```lisp
; Integer arithmetic only
(PLUS 4 4)      ; Returns 10 (octal) = 8 decimal
; No floating point support at all
; Octal arithmetic by default
```

#### 3. Compiler and Advanced Macros
**LISP 1.5:**
```lisp
; Sophisticated compiler system
; 10-100x speedup over interpreter
; SPECIAL/COMMON variable declarations
; Self-bootstrapping compiler
; Advanced macro facilities
```

**PDP-1 Lisp:**
```lisp
; Interpreter only
; No compilation facilities
; Simple function definition only
```

#### 4. Sophisticated I/O
**LISP 1.5:**
```lisp
; Multiple I/O devices
read[]          ; Flexible input parsing
print[x]        ; Formatted output
punch[x]        ; Card punch output
; Comprehensive character handling
```

**PDP-1 Lisp:**
```lisp
; Minimal I/O
READ            ; Basic S-expression input
PRINT           ; Simple output
TYI/TYO         ; Character-level I/O
; Hardware-specific I/O (paper tape, CRT display)
```

## Detailed Function Comparison

### Functions Identical in Both Systems

```lisp
; List processing core
CAR, CDR, CONS, ATOM, NULL, LIST

; Control flow
COND, PROG, GO, RETURN, LAMBDA

; Variable manipulation
SETQ (but different scoping rules)

; I/O basics
READ, PRINT, TERPRI

; Logical operations
LOGAND, LOGOR

; Basic arithmetic
PLUS, MINUS (integers only in PDP-1)
```

### Functions Different Between Systems

#### EQ Function
**LISP 1.5:**
```lisp
; EQ works only on atomic symbols
(EQ 'A 'A)      ; T
(EQ 3 3)        ; Undefined behavior
```

**PDP-1 Lisp:**
```lisp
; EQ works on both atoms AND numbers
(EQ A A)        ; T
(EQ 3 3)        ; T
```

#### GREATERP Function
**LISP 1.5:**
```lisp
; GREATERP tests X ≥ Y
(GREATERP 5 5)  ; T (greater than or equal)
```

**PDP-1 Lisp:**
```lisp
; GREATERP tests X > Y (strict inequality)
(GREATERP 5 5)  ; NIL (strictly greater than)
```

#### Print Functions
**LISP 1.5:**
```lisp
; PRIN1 has specific formatting behavior
(PRIN1 'ATOM)   ; Formatted output with spacing
```

**PDP-1 Lisp:**
```lisp
; PRIN1 prints without extra space, returns NIL
(PRIN1 ATOM)    ; Minimal output, returns NIL
```

### Functions Unique to Each System

#### LISP 1.5 Exclusive Functions
```lisp
; Advanced list processing
APPEND[x; y]    ; Concatenate lists (copies first)
REVERSE[x]      ; Reverse list
SUBST[x; y; z]  ; Substitute throughout structure
SUBLIS[alist; expr] ; Multiple substitutions
COPY[x]         ; Deep copy of structure

; Arithmetic (full numeric tower)
TIMES[x1; ...; xn]     ; Multiplication
QUOTIENT[x; y]         ; Division
REMAINDER[x; y]        ; Modulo
EXPT[x; y]             ; Exponentiation
FLOATP[x], FIXP[x]     ; Type predicates

; Advanced features
MAPLIST[x; fn]         ; Higher-order functions
SEARCH[x; p; f; u]     ; Complex searching
ERRORSET[expr; flag]   ; Error handling
TRACE[fn1; fn2; ...]   ; Debugging support

; Property list manipulation
GET[atom; indicator]
PUTPROP[atom; value; indicator]
REMPROP[atom; indicator]
```

#### PDP-1 Lisp Exclusive Functions
```lisp
; Hardware integration
XEQ             ; Execute machine language instructions
                ; (XEQ C A I) executes instruction C with A in accumulator,
                ; I in I/O register, returns (a i p) where p is skip flag

LOC             ; Returns machine register where atom/list begins
                ; (LOC X) gives memory location of X

; Hardware I/O
TYI/TYO         ; Character-level typewriter I/O
RPA/RPB         ; Paper tape input (alphanumeric/binary)
PPA/PPB         ; Paper tape output (alphanumeric/binary)
DPY             ; CRT display point plotting

; Memory management (manual)
XSY             ; Expunge symbols from OBLIST
REMOVE          ; Remove specific symbols from OBLIST
DEPOSIT         ; Store numbers at memory addresses
PUTSUBR         ; Define machine language subroutine
DEFSUBR         ; Name existing machine routine

; System-specific
STOP            ; Halt with argument (vs PAUSE in 1.5)
GENSYM          ; Generate unique symbols (simpler than 1.5)
```

## Programming Model Differences

### Variable Scoping and Definition

#### LISP 1.5
```lisp
; Global variables via property lists
(SETQ X 42)     ; Creates global binding

; Functions defined via property lists
(DEFINE '((FACTORIAL
  (LAMBDA (N)
    (COND ((ZEROP N) 1)
          (T (TIMES N (FACTORIAL (SUB1 N)))))))))

; Complex scoping with association lists
; Dynamic scoping throughout
```

#### PDP-1 Lisp
```lisp
; NO global variables - variables only in PROG
(SETQ X 42)     ; ERROR: "uss - Unbound symbol in SETQ"

; Variables MUST be declared in PROG
(PROG (X Y)
  (SETQ X 42)   ; Now works
  (RETURN X))

; Function definition via RPLACD
(RPLACD (QUOTE FACTORIAL) (QUOTE
  (EXPR (LAMBDA (N)
    (COND ((ZEROP N) 1)
          (T (TIMES N (FACTORIAL (DIFFERENCE N 1)))))))))
```

### Memory Management Philosophy

#### LISP 1.5
```lisp
; Automatic garbage collection
; Programmer can ignore memory management
; Can write long-running programs
; Focus on algorithmic correctness

(DEFUN INFINITE-COMPUTATION ()
  (PROG ()
    LOOP
    (SETQ DATA (CONS (GENSYM) DATA))  ; Creates garbage freely
    (PROCESS DATA)
    (GO LOOP)))  ; GC will clean up automatically
```

#### PDP-1 Lisp
```lisp
; Manual memory management required
; Programmer must be memory-conscious
; Short-lived programs or careful design
; Explicit cleanup necessary

; Memory-conscious programming
(PROG (DATA TEMP)
  (SETQ DATA (CONS A B))     ; Careful with CONS
  ; ... use data ...
  (REMOVE TEMP)              ; Manual cleanup
  (XSY)                      ; Expunge unused symbols
  (RETURN RESULT))
```

### Error Handling Comparison

#### LISP 1.5
```lisp
; Sophisticated error handling
(ERRORSET '(DIVIDE-BY-ZERO-FUNCTION) T)  ; Graceful recovery
; Comprehensive error diagnostics
; Can continue after most errors
```

#### PDP-1 Lisp
```lisp
; Basic error codes
; icd - Illegal COND
; uss - Unbound symbol in SETQ
; sce - Storage capacity exceeded
; Most errors allow continuation with CONTINUE button
; Storage errors require manual cleanup
```

## Input/Output Differences

### Number Representation

#### LISP 1.5
```lisp
; Decimal default
42          ; Decimal forty-two
3.14159     ; Floating point
6.E2        ; Scientific notation
777Q        ; Octal (explicit)
```

#### PDP-1 Lisp
```lisp
; Octal default
42          ; Octal 42 = decimal 34
777777      ; -0 in 1's complement
777776      ; -1 in 1's complement
DECIMAL     ; Switch to decimal mode
10          ; Now decimal 10
OCTAL       ; Switch back to octal
```

### Interactive Environment

#### LISP 1.5
```lisp
; Batch processing model primarily
; Sophisticated debugging with trace
; Error recovery mechanisms
; Can save/restore program state
```

#### PDP-1 Lisp
```lisp
; Interactive READ-EVAL-PRINT loop
; Hardware debugging (single step, examine/deposit)
; Sense switches for program control
; Direct hardware integration
; Must add space after final parenthesis for input
```

## Historical Significance

### LISP 1.5 Achievements
- Established the "full Lisp" model
- Proved symbolic computation viability on large machines
- Foundation for AI research through 1970s-1980s
- Influenced modern Lisp design (Common Lisp, Scheme)

### PDP-1 Lisp Achievements
- Proved Lisp could work on small machines
- Demonstrated essential vs. optional features
- Showed hardware integration possibilities
- Influenced microcomputer Lisp implementations
- Early example of "subset language" design

## Programming Strategy Differences

### LISP 1.5 Programming
```lisp
; Can use full recursive style
; Memory not a primary concern
; Focus on algorithmic elegance
; Use built-in functions extensively

(DEFUN DEEP-RECURSION (N)
  (COND ((ZEROP N) NIL)
        (T (CONS N (DEEP-RECURSION (SUB1 N))))))
```

### PDP-1 Lisp Programming
```lisp
; Must be memory-conscious
; Prefer PROG over deep recursion
; Manual memory management
; Hardware integration when beneficial

(PROG (N RESULT)
  (SETQ N 10)
  (SETQ RESULT NIL)
  LOOP
  (COND ((ZEROP N) (RETURN RESULT)))
  (SETQ RESULT (CONS N RESULT))
  (SETQ N (DIFFERENCE N 1))
  (GO LOOP))
```

## Conclusion

PDP-1 Lisp represents a masterful distillation of LISP 1.5 down to its essential core. Deutsch and Berkeley successfully identified the minimum viable Lisp:

**Essential Core (Kept):**
- S-expressions and symbolic computation
- Recursive evaluation with EVAL
- Basic list operations (CAR, CDR, CONS)
- Conditional logic (COND)
- Function definition (LAMBDA/LABEL equivalent)

**Advanced Features (Removed):**
- Automatic garbage collection
- Floating-point arithmetic
- Compiler and sophisticated macros
- Complex I/O and character handling

This strategic reduction created a working Lisp that proved the concept could scale down to microcomputers, influencing the design of Lisp implementations throughout the personal computer era. The PDP-1 version demonstrated that the "essence" of Lisp could fit in remarkably small memory footprints while still providing the power of symbolic computation and recursive programming.
