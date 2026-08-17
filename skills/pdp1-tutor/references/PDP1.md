> Agent-side expertise file — **not user-facing tour material**.
> Canonical source (READ-ONLY, never edit there):
> `/home/x/Documents/obso-site/pidp1-sw/PDP1.md`. Copied 2026-08-17.

# PDP-1 Assembly Programming Assistant

## Architecture & Assembler Fundamentals

### PDP-1 Architecture
- **18-bit word machine** (1959) with **1's complement arithmetic**
- **Memory**: 4096 words (0000-7777 octal), expandable to 65,536 words
- **Registers**: AC (Accumulator), IO (In-Out Register), PC (Program Counter)
- **Address format**: 12-bit (0000-7777 octal)
- **Number representation**: Octal by default, 1's complement (-0 = 777777, -1 = 777776)
- **Minus zero handling**: Automatically converted to plus zero (+0) in most operations

**PDP-1 18-bit Word Format:**
- **Bit 0**: Sign bit (0 = positive, 1 = negative)
- **Bits 1-17**: Magnitude bits (Bit 1 = most significant, Bit 17 = least significant)
- **1's complement encoding**: Negative numbers are bitwise complement of positive
- **Note**: Decimal-binary conversion requires subroutines (not built-in hardware)
- **Note**: Floating point requires interpretive programming (software implementation)

### MACRO1 Cross-Assembler Workflow

**Command Syntax:**
```bash
macro1 [-d] [-p] [-m] [-r] [-s] [-x] [-S file] source.mac
```

**Input Files:**
- **`source.mac`** - Your assembly source code (required)
- **`symbols.sym`** - Symbol tape file (optional, with `-S` flag)

**Auto-Generated Output Files:**
- **`program.lst`** - Assembly listing with addresses and machine code (always created)
- **`program.rim`** - Executable binary in RIM format (always created) 
- **`program.prm`** - Permanent symbols dump (with `-p` flag)
- **`program.sym`** - Symbol table dump (with `-s` flag)

**Essential Assembly Flags:**
- **`-d`** - Dump symbol table (essential for debugging) - **USE THIS**
- **`-x`** - Cross-reference listing (shows where symbols are used)
- **`-m`** - Show macro expansions in listing
- **`-p`** - Generate permanent symbols file
- **`-s`** - Generate symbol tape output

**Most common usage:** `macro1 -d program.mac` (assemble with symbol dump)

**Source Line Format:**
```
[LABEL,] [INSTRUCTION] [OPERAND] [;COMMENT]
```

**IMPORTANT: Labels are limited to 6 characters maximum.** The assembler truncates longer labels, which can cause duplicate symbol errors (e.g., `endname` and `endloop` both become `endnam` and `endloo`).

**Label Requirements:**
- Maximum 6 characters
- Must end with comma (,) if present
- First character must be letter
- Can contain letters, digits, and some special characters

**Comment Formatting Rules:**
- **Line comments**: Start line with `/` (e.g., `/ This is a comment`)
- **Inline comments**: Must use TAB separation, not spaces
  ```
  INSTRUCTION<TAB>OPERAND<TAB><TAB>/<SPACE>COMMENT
  ```
- **CRITICAL**: Using spaces instead of tabs for inline comment alignment causes "illegal character" errors
- **Example**: `lac word		/ load the word` (tabs before `/`)
- **Wrong**: `lac word         / load the word` (spaces cause assembly errors)

**Critical Syntax Rules:**
1. **Labels end with comma**: `LOOP, LAC X` (not `LOOP LAC X`)
2. **Symbols max 6 chars**: `SYMBOL` not `VERYLONGSYMBOL`
3. **Octal by default**: `777` = 511 decimal, `10` = 8 decimal
4. **Indirect addressing**: `LAC I PTR` (not `LAC (PTR)`)
5. **Case insensitive** but consistent style recommended

**Essential Pseudo-Instructions:**
```assembly
START address    ; Set program entry point (required)
DECIMAL         ; Switch to decimal mode
OCTAL           ; Switch to octal mode (default)  
EXPUNGE         ; Clear symbol table (for multi-pass assembly)
```

**Symbol Definition Patterns:**
```assembly
; Data definition (creates storage)
LABEL,    12345    ; Define word with value 12345
BUFFER,   0        ; Reserve word, initialize to 0
ARRAY,    1        ; First element of array
          2        ; Subsequent elements (no label)
          3
          
; Symbolic constants (no storage created)  
TABLE = 1000       ; Define symbolic constant (equals 1000)
SIZE = 20          ; Another constant

; Usage examples
        LAC LABEL  ; Load the value stored at LABEL
        LAC TABLE  ; Load immediate value 1000 (the constant)
        DAC BUFFER ; Store to the reserved location
```

**Base Control Workflow:**
```assembly
        OCTAL      ; Default mode (numbers interpreted as octal)
        LAW 10     ; Loads octal 10 = decimal 8
        
        DECIMAL    ; Switch to decimal mode  
        LAW 10     ; Loads decimal 10
        DAC TEMP   ; Store decimal 10
        
        OCTAL      ; Switch back to octal
        LAW 12     ; Loads octal 12 = decimal 10 (same value as above)
        
TEMP,   0          ; Storage location
```

## Complete Instruction Reference

### Instruction Format & Addressing

**PDP-1 Instruction Word Layout:**
```
Bit:  0-4    5    6-17
     [OP ] [I] [ADDRESS]
      └─────┘ │ └─────────┘
     Operation│  12-bit Address/Operand
     Code     │  (0000-7777 octal)
              │
              Indirect Bit (defer addressing)
```

**Addressing Modes:**
- **Direct**: `LAC 100` → load from address 100
- **Indirect**: `LAC I 100` → load from address stored at 100 (+5μs per level)
- **Immediate**: `LAW 123` → load literal value 123

**CRITICAL**: The I-bit (bit 5) controls indirection and has special meanings:
- **Memory instructions**: Enables indirect addressing
- **Skip instructions**: **INVERTS** the skip condition
- **I/O instructions**: Controls completion pulse waiting

### Memory Reference Instructions (10 μsec)

#### Data Transfer
```assembly
LAC Y    ; Load AC from address Y, destroys original AC
DAC Y    ; Store AC to address Y
LIO Y    ; Load IO register from address Y
DIO Y    ; Store IO register to address Y
DZM Y    ; Store zero at address Y
DAP Y    ; Deposit AC bits 6-17 to Y bits 6-17 (address part only)
DIP Y    ; Deposit AC bits 0-5 to Y bits 0-5 (instruction part only)
XCT Y    ; Execute instruction stored at Y (skips execute in place)
```

#### Arithmetic (10 μsec, except MUL/DIV)
```assembly
ADD Y    ; AC = AC + C(Y), sets overflow on signed overflow
SUB Y    ; AC = AC - C(Y), sets overflow on signed overflow
IDX Y    ; C(Y) = C(Y) + 1, result also stored in AC
ISP Y    ; C(Y) = C(Y) + 1, skip next instruction if result positive

; Advanced Arithmetic (requires hardware option)
MUL Y    ; AC:IO = AC * C(Y), 34-bit result (14-25μs)
DIV Y    ; AC = quotient, IO = remainder (30-40μs, 12μs on overflow)
```

**CRITICAL MUL/DIV Details:**
- **MUL produces 34-bit result**: magnitude in AC(1-17):IO(0-16), signs in both AC(0) and IO(17)
- **DIV requires dividend in AC:IO format**, skips next instruction unless overflow
- **DIV overflow**: occurs when |dividend_high| ≥ |divisor|, restores original AC:IO

#### Logical Operations (10 μsec)
```assembly
AND Y    ; AC = AC & C(Y), bitwise AND
IOR Y    ; AC = AC | C(Y), bitwise inclusive OR
XOR Y    ; AC = AC ^ C(Y), bitwise exclusive OR
```

#### Control Flow (5-10 μsec)
```assembly
JMP Y    ; Jump to address Y
JSP Y    ; Jump to Y, save return address + flags in AC, DESTROYS original AC
JDA Y    ; Store AC at Y, jump to Y+1, save return address + flags in AC
CAL      ; Store AC at 100, jump to 101, save return address + flags in AC. Equal to JDA 100.
```

#### Memory Comparison (10 μsec)
```assembly
SAD Y    ; Skip next instruction if AC ≠ C(Y)
SAS Y    ; Skip next instruction if AC = C(Y)
```

### Augmented Instructions (5 μsec)

#### Immediate Load
```assembly
LAW N    ; Load AC with immediate value N (0-4095)
LAW I N  ; Load AC with immediate value -N (1's complement)
```

#### Shift and Rotate Group (5 μsec)
**CRITICAL**: Count determined by number of 1-bits in instruction bits 9-17

```assembly
; Accumulator Operations
RAR 4S   ; Rotate AC right 4 positions
RAL 3S   ; Rotate AC left 3 positions
SAR 2S   ; Shift AC right 2 positions (arithmetic)
SAL 1S   ; Shift AC left 1 position (arithmetic)

; IO Register Operations
RIR 4S   ; Rotate IO right 4 positions
RIL 3S   ; Rotate IO left 3 positions
SIR 2S   ; Shift IO right 2 positions
SIL 1S   ; Shift IO left 1 position

; Combined 36-bit Operations
RCR 4S   ; Rotate AC:IO combined right 4 positions
RCL 3S   ; Rotate AC:IO combined left 3 positions
SCR 2S   ; Shift AC:IO combined right 2 positions
SCL 1S   ; Shift AC:IO combined left 1 position
```

**CRITICAL - Shift Constants:**
- **MUST use S-suffix**: `1S`, `2S`, `3S`, `4S`, `5S`, `6S`, `7S`, `8S`, `9S`
- **NEVER use plain numbers**: `SAR 4` ≠ `SAR 4S`
- **Encoding**: 1S=1, 2S=3, 3S=7, 4S=17, etc. (number of bits set)

**Shift Instruction Bit Encoding (explains S-constants):**
- **Bit 5**: Direction (0 = right, 1 = left)
- **Bit 6**: Type (0 = logical, 1 = arithmetic)
- **Bits 7-8**: Register selection (01 = AC only, 10 = IO only, 11 = both AC:IO)
- **Bits 9-17**: Step count (number of 1-bits in these positions = shift steps)
  - This explains why: 1S=1, 2S=3, 3S=7, 4S=17, 5S=37, etc.

#### Skip Group Instructions (5 μsec)
**Can be combined with inclusive OR for multiple conditions**

```assembly
; Accumulator Tests
SZA      ; Skip if AC = +0 (zero)
SPA      ; Skip if AC ≥ 0 (positive, including +0)
SMA      ; Skip if AC < 0 (negative, including -0)

; IO Register Test
SPI      ; Skip if IO ≥ 0 (positive)

; System Status Tests
SZO      ; Skip if overflow = 0 AND clear overflow flag
SZF n    ; Skip if program flag n = 0 (n = 1-6, 7 = all flags)
SZS n    ; Skip if sense switch n = 0 (n = 1-6, 7 = all switches)
```

**CRITICAL Skip Instruction Rules:**
- **Skip instructions can be combined** with inclusive OR for multiple conditions in single instruction
- **With indirect bit set (I)**: All skip conditions are **INVERTED**
  - `SZA I` = skip if AC is **NOT** zero
  - `SMA I` = skip if AC is **NOT** minus  
  - `SZO I` = skip if overflow is **NOT** zero

#### Operate Group Instructions (5 μsec)
**Can be combined with inclusive OR for multiple operations**

```assembly
CLA      ; Clear AC (set to +0)
CMA      ; Complement AC (1's complement)
HLT      ; Halt computer
CLI      ; Clear IO register
NOP      ; No operation
LAT      ; Load AC with Test Word (console switches) - usually with CLA
LAP      ; Load AC with Program Counter + flags - usually with CLA
CLF n    ; Clear program flag n (n = 1-6, 7 = all flags)
STF n    ; Set program flag n (n = 1-6, 7 = all flags)
```

**Console Hardware Integration:**
- **LAT instruction**: Reads 18-bit Test Word from console switches into AC
- **SZS n instruction**: Tests individual Sense Switches (n = 1-6)
  - SZS 1 through SZS 6 test individual switches
  - SZS 7 tests all switches (skip only if all are 0)
- **Program Flags**: 6 independent flags for I/O synchronization
  - Set by STF instruction or I/O device completion
  - Cleared by CLF instruction  
  - Tested by SZF instruction

**Examples of combined operations:**
```assembly
760300   ; CLA + CMA (clear then complement = load -0)
760700   ; CLA + CMA + HLT (clear, complement, halt)
```

### Input/Output Transfer Group (IOT - 5 μsec without wait)

#### Control Bits
- **Bit 5 (I-bit)**: 1 = wait for completion pulse, 0 = no wait
- **Bit 6**: Together with bit 5 determines completion pulse handling
- **Bits 12-17**: Device selection (001-007 for standard devices)

#### Standard I/O Devices
```assembly
; Perforated Tape Reader
RPA      ; Read Perforated Tape Alphanumeric (8-bit to IO bits 10-17)
RPB      ; Read Perforated Tape Binary (18-bit word from 3 lines)
RRB      ; Read Reader Buffer (transfer buffered data to IO)

; Perforated Tape Punch
PPA      ; Punch Perforated Tape Alphanumeric (IO bits 10-17)
PPB      ; Punch Perforated Tape Binary (IO bits 0-5, plus holes 7&8)

; Alphanumeric Typewriter
TYO      ; Type Out (character from IO register bits 12-17)
TYI      ; Type In (character to IO register bits 12-17, sets Program Flag 1)

#### Detailed Typewriter Operation

**Type Out (TYO) - Address 0003**
- **Function**: Outputs one character per instruction
- **Character source**: Right 6 bits of IO Register (bits 12-17)  
- **Usage**: Load character into IO register, then execute TYO
```assembly
lio char    ; Load character into IO register  
tyo         ; Type out character from IO register
```

**Type In (TYI) - Address 0004**  
- **Function**: Asynchronous character input from typewriter
- **Operation sequence**:
  1. When typewriter key is struck:
     - Character code placed in typewriter buffer
     - **Program Flag 1 is SET** (indicates character ready)
     - Type-in status bit set to 1
  2. Program checks Program Flag 1 periodically
  3. When flag 1 is set, execute TYI instruction
  4. **TYI automatically**:
     - Clears IO register before transfer
     - Transfers character to IO register bits 12-17
     - Clears type-in status bit
     - **Clears Program Flag 1**

**Critical TYI Programming Pattern**:
```assembly
inloop, cla         ; Clear accumulator
        cli         ; Clear IO register  
        szs 1       ; Skip if program flag 1 is SET
        jmp inloop  ; Flag clear, keep waiting
        tyi         ; Flag set, read character (clears flag 1)
        ; Character now in IO register bits 12-17
        dio temp    ; Save character if needed
        lac temp    ; Load to AC for testing
        tyo         ; Echo character back to user
```

**Key Points**:
- **Wait for flag 1 to be SET** (not cleared) before executing TYI
- **TYI clears flag 1 automatically** - don't clear it manually
- **Use SZS 1** (skip if set) not SZF 1 (skip if zero) to test flag
- **Character input is asynchronous** - must check flag before reading
- **No I/O wait needed** - TYI should not use optional in-out wait

; CRT Display (Type 30)  
DPY      ; Display point: AC bits 0-9 = X, IO bits 0-9 = Y
         ; Intensity in instruction bits 9-11 (1's complement encoding)
         ; 3 = brightest, 0 = default/normal, 7 = barely visible (-0 in 1's complement)

; System Control
ESM      ; Enter Sequence Break Mode (enable interrupts)
LSM      ; Leave Sequence Break Mode (disable interrupts)
CBS      ; Clear Sequence Break System
CKS      ; Check Status (device status to IO register)
```

**CRITICAL I/O Notes:**
- **MACRO assembler I/O instructions** (RPA, RPB, PPB, TYO, DPY) have I-bit included by default
- **Use `DPY-I` syntax** for plain DPY without completion pulse wait  
- **DPY intensity encoding**: Instruction bits 9-11 use 1's complement
  - `3` = brightest display
  - `0` = default/normal intensity
  - `7` = barely visible (-0 in 1's complement)
  - Requires manual instruction bit manipulation for non-default intensities

## Programming Patterns & Examples

### Program Structure Template
```assembly
        START MAIN

MAIN,   ; Your main program logic here
        HLT

; Data section
VAR1,   0
VAR2,   123
CONST,  777
```

### Loop Patterns
```assembly
; Basic counting loop
START MAIN

MAIN,   LAC COUNT     ; Initialize counter
LOOP,   SAD LIMIT     ; Test against limit
        JMP DONE      ; Exit if equal
        ; ... loop body ...
        LAC COUNT     ; Load counter
        ADD ONE       ; Increment
        DAC COUNT     ; Store back
        JMP LOOP      ; Continue

DONE,   HLT

COUNT,  0             ; Loop variable
LIMIT,  12            ; Loop limit (octal 12 = decimal 10)
ONE,    1

; Index-based loop (more efficient)
        LAC MINUS10   ; Load negative count
        DAC COUNT
LOOP,   ISP COUNT     ; Increment and skip if positive
        JMP LOOP      ; Continue if negative
        ; Loop complete

COUNT,  0
MINUS10, 777766      ; -10 in 1's complement
```

### Subroutine Calling Patterns

#### JSP Pattern (Simple Calls - No Parameters)
```assembly
        JSP SUBR      ; Jump to SUBR, DESTROYS AC, saves return address in AC
        ; ... execution continues here ...

SUBR,   DAC SUBR      ; MUST store return address immediately
        ; ... subroutine body (original AC contents lost) ...
        JMP I SUBR    ; Return via indirect jump
```

#### JDA Pattern (Parameter Passing)
```assembly
        LAC PARAM     ; Load parameter value into AC
        JDA SUBR      ; Store PARAM at SUBR, jump to SUBR+1, save return in AC
        ; ... execution continues here ...

SUBR,   0             ; Parameter storage (receives PARAM value)
        DAC SUBR+1    ; Store return address
        LAC SUBR      ; Load the passed parameter
        ; ... subroutine body using parameter ...
        JMP I SUBR+1  ; Return via stored address
```

#### CAL Pattern (Master System Call)
```assembly
        LAC PARAM     ; Load parameter to pass to system routine
        CAL           ; Store PARAM at 100, jump to 101, save return in AC
        ; ... execution continues here ...

; Master system routine at FIXED location 101:
101,    DAC 102       ; Save return address immediately
        LAC 100       ; Load parameter passed via CAL
        ; ... system routine body ...
        JMP I 102     ; Return via saved return address
102,    0             ; Return address storage
```

### Arithmetic Examples

#### Multiply/Divide Handling
```assembly
; Multiply example
        LAC MULTI1    ; Load multiplicand
        MUL MULTI2    ; AC:IO = MULTI1 * MULTI2
        ; Result: magnitude in AC(1-17):IO(0-16), sign in AC(0) and IO(17)

; Divide example
        LAC DIVHIGH   ; Load high dividend
        LIO DIVLOW    ; Load low dividend
        DIV DIVISOR   ; AC = quotient, IO = remainder
        JMP NOOVF     ; This instruction skipped if no overflow
        ; ... handle overflow case ...
NOOVF,  ; ... use quotient in AC, remainder in IO ...
```

#### Error Handling Pattern
```assembly
        ADD VALUE     ; Perform addition
        SZO           ; Skip if no overflow (and clear overflow flag)
        JMP OVFLERR   ; Handle overflow error
        ; ... continue with normal processing ...
```

### Conditional Logic Patterns
```assembly
; Simple comparison
        LAC VALUE     ; Load test value
        SAD ZERO      ; Compare with zero
        JMP NONZERO   ; Branch if not zero
        ; ... zero case ...
        JMP CONTINUE
NONZERO,; ... non-zero case ...
CONTINUE,

; Memory comparison
        LAC VAL1      ; Load first value
        SAD VAL2      ; Skip if different from VAL2
        JMP EQUAL     ; They are equal
        ; ... not equal case ...
        JMP DONE
EQUAL,  ; ... equal case ...
DONE,   
```

### I/O Programming Examples
```assembly
; Simple typewriter output
        LAC MESSAGE   ; Load character
        DAC IO        ; Store in IO for output
        TYO           ; Type character
        
; CRT display point
        LAC XCOORD    ; Load X coordinate
        LIO YCOORD    ; Load Y coordinate  
        DPY           ; Display point

; Paper tape input
        RPA           ; Read alphanumeric character
        LAC IO        ; Get character from IO register
```

## Critical AI Programming Rules

### Illegal Instructions (cause processor HALT)
**NEVER use these opcodes:** 00, 12, 14, 36, 74

### Instruction Behavior Warnings
1. **JSP destroys AC** - use JDA for parameter passing
2. **XCT skips execute in place** - not after the XCT instruction
3. **MUL/DIV require specific register setup** - dividend in AC:IO for DIV
4. **Shift counts use bit-encoding** - never use plain numbers, always use 1S-9S constants
5. **Skip with I-bit inverts condition** - SZA I = skip if NOT zero
6. **Operate/Skip instructions can combine** - use inclusive OR of addresses
7. **CAL uses fixed locations** - always 100 for parameter, 101 for entry

### Memory Organization Rules
1. **Page 0 (0000-0377)**: Reserved for system use - avoid for user programs
   - **Locations 0-2**: Sequence Break storage (AC, PC, IO during interrupts)
   - **Locations 100-101**: CAL subroutine parameter and entry point
2. **Program start**: Use START directive, typically **0400 or higher** to avoid system areas
3. **Data area**: Place after code to avoid conflicts
4. **Page boundaries**: Consider 4K page limits for large programs (0000-7777)

### Number Representation Rules
1. **Default octal**: `10` = 8 decimal, `100` = 64 decimal
2. **1's complement**: `777777` = -0, `777776` = -1
3. **Minus zero conversion**: Most operations automatically convert -0 to +0
4. **Use DECIMAL/OCTAL** pseudo-ops to change base temporarily

### Common AI Mistakes to Avoid
1. **Wrong address format**: Use `100` not `0x100` or `100h`
2. **Missing comma on labels**: `LOOP LAC X` → `LOOP, LAC X`
3. **Decimal in octal mode**: `10` = 8 decimal, use `DECIMAL` or `12` for 10 decimal
4. **Long symbol names**: `VERYLONGNAME` → `VLONG` (6 char max)
5. **Wrong indirection**: `LAC (PTR)` → `LAC I PTR`
6. **Skip instruction confusion**: `SAD` skips if different, `SAS` skips if same
7. **Shift instruction errors**: `SAR 4` ≠ `SAR 4S` - always use S-suffix constants
8. **Register confusion**: TYO/TYI use IO register, not AC
9. **DPY coordinate format**: X in AC bits 0-9, Y in IO bits 0-9

### Assembly Error Codes & Debugging Process
**Common Assembly Errors:**
- **DT** - Duplicate Tag (symbol defined twice)
- **IC** - Illegal Character (invalid character in source)
- **UA** - Undefined Address (symbol referenced but not defined)
- **IR** - Illegal Reference (off-page address reference)
- **PE** - Page Exceeded (program exceeds available memory)

**Debugging Workflow:**
1. **Always use `-d` flag** for symbol table dump
2. **Check `.lst` file** for addresses and machine code generation
3. **Use `-x` flag** for cross-reference to find where symbols are used
4. **Use `-m` flag** if using macros to see expansions
5. **Common fixes:**
   - **DT error**: Check for duplicate labels (remember labels end with comma)
   - **UA error**: Check spelling of symbol names (6 chars max, case insensitive)
   - **IC error**: Check for invalid characters, ensure proper comma after labels
   - **IR error**: Check address references don't exceed memory limits

### Timing Considerations
- **Memory reference**: 10 μsec
- **Multiply**: 14-25 μsec
- **Divide**: 30-40 μsec (12 μsec on overflow)
- **Operate/Skip/Shift**: 5 μsec
- **Jump**: 5 μsec
- **Indirect addressing**: +5 μsec per level
- **I/O with wait**: Variable time until completion pulse
- **Sequence break**: 15 μsec interrupt handling overhead

## Quick Reference Templates

### Most Common Instructions
```assembly
LAC/DAC  ; Load/store accumulator
LAW      ; Load immediate value  
ADD/SUB  ; Arithmetic
JMP/JSP  ; Control flow
SAD/SAS  ; Comparison
SMA/SPA  ; Sign test
CLA      ; Clear accumulator
HLT      ; Stop program
```

### Complete Working Example
```assembly
        START MAIN

MAIN,   LAC NUM1      ; Load first number
        ADD NUM2      ; Add second number  
        DAC RESULT    ; Store result
        HLT           ; Stop program

NUM1,   123           ; First operand
NUM2,   456           ; Second operand  
RESULT, 0             ; Sum storage
```

**To assemble and run:**
```bash
macro1 -d example.mac     # Creates example.lst and example.rim
# Load example.rim into PDP-1 simulator or hardware
# Program will add 123 + 456 = 601 (octal) and halt
```

### Development and Debugging Features

**Console Operations:**
- **EXAMINE**: Display memory contents in AC/Memory Buffer lights
- **DEPOSIT**: Store Test Word value into specified memory location
- **SINGLE STEP**: Execute one instruction at a time for debugging
- **SINGLE INST**: Execute one memory cycle at a time
- **START**: Begin execution from Address Switches location
- **CONTINUE**: Resume execution from current Program Counter location

**Built-in Diagnostics:**
- **Marginal checking circuits**: Hardware reliability testing
- **Register indicator lights**: Grouped for convenient octal reading
- **Console switches**: Address (16-bit), Test Word (18-bit), Sense (6-bit)

**Programming Debug Techniques:**
```assembly
        START MAIN

MAIN,   ; Add -d flag to macro1 for symbol dump
        ; Use SAD/SAS for conditional breakpoints
        ; Check overflow with SZO after arithmetic  
        ; Use LAP to examine program counter
        ; Use LAT to read console switches for input
        ; Use STF/CLF and SZF for program flow control
        HLT
```

## PDP-1 Programming Architecture Summary

**Key Programming Strengths:**
- **15 basic skip instructions** (combinable with inclusive OR for complex conditions)
- **3 subroutine calling methods** (JSP, JDA, CAL for different use cases)
- **12 shift/rotate variations** (single register or combined 36-bit operations)
- **Unlimited indirect addressing levels** (each level adds 5μs)
- **Micro-coded operate instructions** (combinable for powerful single operations)
- **Boolean operations** (AND, IOR, XOR for bit manipulation)
- **Built-in multiply/divide** (hardware option, ~20μs and ~35μs respectively)

This comprehensive reference provides everything needed for PDP-1 assembly programming, from basic syntax through advanced patterns and critical pitfalls to avoid.
