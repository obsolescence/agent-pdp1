> Agent-side expertise file — **not user-facing tour material**.
> Canonical source (READ-ONLY, never edit there):
> `/home/x/Documents/obso-site/pidp1-sw/learnings.md`. Copied 2026-08-17.

# PDP-1 Assembly Programming Learnings

## Critical Syntax Requirements for MACRO1_1 Assembler

### **NEW: Critical Comment Formatting Rules** ⚠️

**CRITICAL DISCOVERY**: PDP-1 assembly has strict formatting requirements for inline comments:

- **Inline comments MUST use TAB separation, not spaces**
- **Format**: `INSTRUCTION<TAB>OPERAND<TAB><TAB>/<SPACE>COMMENT`
- **Using spaces instead of tabs causes "illegal character at column N" errors**

```assembly
/ ✅ CORRECT - uses tabs:
        lac word		/ load the word
        dac temp		/ store temporarily

/ ❌ WRONG - uses spaces (causes assembly errors):
        lac word         / load the word  
        dac temp         / store temporarily
```

**Why this matters**: The assembler expects proper field separation with tabs. Spaces in the comment alignment area are treated as illegal characters.

### **Label Length Restrictions** ⚠️

**CRITICAL**: Labels are limited to **6 characters maximum**. The assembler truncates longer labels, causing duplicate symbol errors.

```assembly
/ ❌ THESE BECOME THE SAME LABEL:
endname,  ...    ; truncated to "endnam"  
endloop,  ...    ; truncated to "endloo"

/ ✅ CORRECT - 6 characters or less:
endinp,   ...    ; "endinp" - exactly 6 chars
done,     ...    ; "done" - under limit
```

## Critical Syntax Requirements for MACRO1_1 Assembler

### File Structure Format
```assembly
/ comment line starting with slash
400/                    ; Origin directive with trailing slash
main,   lac variable    ; Code starts immediately after origin
        dac storage
        ; ... program body ...
        
data,   123            ; Data section

start main             ; Start directive at END of file
```

**Key Rules:**
1. **Comments use `/`** - NOT semicolons like modern assemblers
2. **Origin directive ends with `/`** - Format: `address/` 
3. **Start directive goes at END** - Last line: `start label`
4. **Instructions are lowercase** - `lac`, `dac`, `jmp`, not `LAC`, `DAC`, `JMP`

### MACRO1_1 vs MACRO1_0 Format Differences

**MACRO1_0 Format (OLD - causes BIN loader to loop at 7751):**
```assembly
        start main
main,   lac variable
```

**MACRO1_1 Format (CORRECT for this assembler):**
```assembly
/ comment
400/
main,   lac variable
        ; ... code ...
start main
```

**Problem**: BIN loader loops at address 7751  
**Cause**: Using MACRO1_0 syntax format instead of MACRO1_1 format  
**Solution**: Use proper MACRO1_1 format with `/` comments, `address/` origin, and `start` at end

### Memory Layout Considerations

**Reserved System Areas:**
- **0000-0002**: Sequence Break storage (interrupt handling)
- **0100-0101**: CAL instruction parameter/entry points  

**Safe User Program Areas:**
- **0200+ (octal)**: Safest user program space
- **Use `200/` as standard origin** to avoid CAL conflicts

### Working Hello World Template
```assembly
/ hello world program
400/
main,   lac msgptr     ; Load message pointer
        dac ptr        ; Store in working pointer
        
loop,   lac i ptr      ; Load character indirectly
        sza            ; Skip if zero (end marker)
        jmp output     ; Not zero, go output it
        hlt            ; Zero found, halt program
        
output, lio i ptr      ; Load character to IO register
        tyo            ; Type out to console
        isp ptr        ; Increment pointer, skip if positive
        jmp loop       ; Continue loop
        
ptr,    0              ; Working pointer storage

msgptr, msg            ; Pointer to message start
msg,    110            ; 'H' (octal ASCII)
        145            ; 'e' 
        154            ; 'l'
        154            ; 'l'
        157            ; 'o'
        040            ; ' ' (space)
        167            ; 'w'
        157            ; 'o'
        162            ; 'r'
        154            ; 'l'
        144            ; 'd'
        015            ; CR (carriage return)
        012            ; LF (line feed)
        0              ; End marker

start main
```

### Character Encoding for cross-compiled source code
- **Use octal ASCII values** for characters
- **Common values**: 'H'=110, 'e'=145, 'l'=154, ' '=040
- **Line endings**: CR=015, LF=012
- **Zero terminator**: 0 for end of string

### Assembly Process
```bash
macro1_1 -d program.mac  # Assembles to program.lst and program.rim
```
- **-d flag**: Essential for symbol table dump
- **Output files**: `.lst` (listing), `.rim` (binary for PDP-1)

### Key Differences from Modern Assemblers
1. **Origin at top, start at bottom** - Reverse of many assemblers
2. **Slash comments** - Not semicolons
3. **Trailing slash on origin** - `200/` not just `200`
4. **Lowercase instructions** - Hardware mnemonics are lowercase
5. **Assembler version matters** - MACRO1_1 has different syntax than MACRO1_0

### Debugging Tips
1. **Check .lst file** for actual addresses and opcodes generated
2. **Verify proper MACRO1_1 format** - origin/, comments with /, start at end
3. **Use working examples** like circle-angelo.mac as templates
4. **If BIN loader loops at 7751** - check file format, not program address

### PDP-1 Character Encoding and Typewriter I/O

**Critical Discovery: FIODEC 6-bit Character Packing**

The PDP-1 typewriter uses **6-bit FIODEC character encoding**, not 8-bit ASCII:
- **3 characters packed per 18-bit word** (6 bits each)
- **Use `text "string"` directive** - assembler automatically packs characters
- **Characters extracted using rotation** - `rcl 6s` moves 6 bits from AC to IO register

**Correct Typewriter Output Pattern:**
```assembly
lup,    lac i ptr       ; Load packed word from message
        cli             ; Clear IO register  
lu2,    rcl 6s          ; Rotate left 6 bits (AC→IO)
        tyo             ; Type character from IO bits 12-17
        sza             ; Skip if AC now zero (all chars extracted)
        jmp lu2         ; Continue with next char in same word
        idx ptr         ; Move to next packed word
        sas end         ; Skip if past end marker
        jmp lup         ; Continue with next word
        hlt             ; Halt when done
```

**Working Hello World Template:**
```assembly
/ hello world program
400/
lup,    lac i ptr       ; Load packed word
        cli             ; Clear IO register
lu2,    rcl 6s          ; Extract 6-bit character
        tyo             ; Type out character
        sza             ; Check if word exhausted
        jmp lu2         ; Continue current word
        idx ptr         ; Next word
        sas end         ; Check end
        jmp lup         ; Continue message
        hlt             ; Halt

ptr,    msg             ; Message pointer
msg,    text "hello world"  ; Packed 6-bit FIODEC text
end,    .               ; End sentinel
start 400
```

**Key Character Encoding Facts:**
- **6-bit FIODEC encoding** - Not 8-bit ASCII
- **3 characters per 18-bit word** - Efficient packing
- **`text` directive** - Assembler handles character packing automatically
- **Rotation extraction** - `rcl 6s` shifts 6 bits from AC to IO register
- **Sentinel marker** - Use `.` for end of message, not zero

## Lessons Learned
- **Assembler format is critical** - Wrong format causes BIN loader failures at 7751
- **MACRO1_1 requires specific syntax** - Different from MACRO1_0 and modern assemblers
- **Case sensitivity matters** - Instructions must be lowercase for this assembler
- **File format structure is rigid** - Origin at top, start at bottom, specific comment syntax
- **System compatibility** - Use proper memory addresses to avoid CAL conflicts
- **Character encoding is unique** - PDP-1 uses 6-bit FIODEC, not ASCII, packed 3 per word
- **Text output requires rotation** - Must extract characters using `rcl 6s` bit shifting
- **Use assembler text directives** - `text "string"` handles character packing automatically

### Space Character Handling in FIODEC

**Critical Issue with Zero-Testing:**
- **Space character = 0 in FIODEC** encoding
- **Zero-testing with `sza` fails** for strings containing spaces
- **"hello world" becomes "helloworld"** - space is skipped as zero

**Solution: Character Counting Instead of Zero-Testing:**
```assembly
lup,    lac i ptr       ; Load packed word from message
        dac word        ; Save the word
        cli             ; Clear IO register
        law 3           ; Load 3 (count 3 chars per word)
        dac count       ; Store counter
lu2,    lac word        ; Reload the word
        lio word        ; Also load into IO register
        rcl 6s          ; Rotate combined AC + IO reg 6 bits left
        dac word        ; Save remaining characters
        tyo             ; Type out character in IO reg bits 12-17
        lac count       ; Load counter
        sub one         ; Subtract 1
        dac count       ; Store back
        sza             ; Skip if zero (done with word)
        jmp lu2         ; Continue with next character in word
```

**Key Insight:** Count characters per word (always 3) instead of testing for zero termination.

### Carriage Returns and Line Endings

**FIODEC Carriage Return:**
- **Carriage return = 077 (octal) in FIODEC**
- **Not ASCII 015** - different encoding system
- **Multiple CRs for spacing:** `777777` = three carriage returns packed in one word

**Line Ending Examples:**
```assembly
msg,    text "hello world"
        777777          ; Three carriage returns (077+077+077)
        text "what is your name?"
        077000000       ; Single CR + padding
```

### Interactive Input with Typewriter (TYI)

**Input Challenge:** TYI instruction requires program flag synchronization

**Working Input Pattern (from DDT analysis):**
```assembly
input,  dac input       ; Save return address

inloop, cla             ; Clear accumulator
        cli             ; Clear IO register  
        clf 1           ; Clear program flag 1
        szf 1           ; Skip if program flag 1 is zero
        jmp .+2         ; Flag is set, continue
        jmp .-2         ; Flag is clear, keep checking
        tyi             ; Read character (sets flag 1)
        
        dio temp        ; Save character from IO to temp
        lac temp        ; Load character to AC for testing
        tyo             ; Echo character back to user
        
        sad cret        ; Skip if NOT carriage return (FIODEC 077)
        jmp inloop      ; Not CR, continue reading
        jmp i input     ; CR found, return from subroutine

temp,   0               ; Temporary storage for character
cret,   077             ; Carriage return in FIODEC
```

**Key Input Concepts:**
- **Program flag synchronization** - Must check flag 1 before TYI
- **Character echo** - TYO echoes input back to user
- **FIODEC 077** - Carriage return for input termination
- **Character storage** - Use DIO to save input character

### Complete Interactive Program Structure

**Final Working Pattern:**
```assembly
/ hello world program
400/
lup,    lac i ptr       ; Main print loop
        dac word
        cli
        law 3
        dac count
lu2,    lac word
        lio word
        rcl 6s
        dac word
        tyo
        lac count
        sub one
        dac count
        sza
        jmp lu2
        idx ptr
        sas end
        jmp lup

        jsp input       ; Call input subroutine
        
        lac greeting    ; Print greeting after input
        dac ptr
        jmp lup

        hlt

ptr,    msg
word,   0
count,  0
one,    1
msg,    text "hello world"
        777777
        text "what is your name?"
end,    .
        077077077

/ Input subroutine
input,  dac input
inloop, cla
        cli
        clf 1
        szf 1
        jmp .+2
        jmp .-2
        tyi
        dio temp
        lac temp
        tyo
        sad cret
        jmp inloop
        jmp i input

temp,   0
cret,   077
greeting, greetmsg
greetmsg, text "Hello again!"
        077000000
        .

start 400
```

**Program Flow:**
1. Print "hello world" with carriage returns
2. Print "what is your name?"
3. Call input subroutine that waits for user input
4. Echo each character typed
5. Wait for carriage return to end input
6. Print "Hello again!" greeting
7. Halt

### Major Debugging Discoveries

**Problem: Space Characters Disappearing**
- **Cause:** Space = 0 in FIODEC, zero-testing skipped spaces
- **Solution:** Count characters per word instead of testing for zero

**Problem: No Carriage Returns Visible**
- **Cause:** Using ASCII carriage return values instead of FIODEC 077
- **Solution:** Use FIODEC encoding, 777777 for multiple CRs

**Problem: Input Not Working**
- **Cause:** Improper TYI flag handling, memory corruption
- **Solution:** Follow DDT pattern with proper flag synchronization

**Problem: Garbage Characters After Text**
- **Cause:** Print loop continuing past intended message boundary
- **Solution:** Place end sentinel (.) before carriage return data

### Research Methods That Worked

1. **Examine macro1.c source** - Found FIODEC encoding table
2. **Study working examples** - hello2.mac, circle-angelo.mac for syntax
3. **Analyze DDT patterns** - ddt.mac for proven input handling
4. **Incremental testing** - Build on working code, don't break what works
5. **Character counting** - More reliable than zero-testing for FIODEC

### Advanced Concepts Discovered

- **Subroutine calls** - JSP instruction saves return address
- **Indirect addressing** - `jmp i input` returns from subroutine
- **Memory layout planning** - Avoid system areas, use 400+ addresses
- **Character extraction techniques** - Rotation with bit manipulation
- **Program flag usage** - Synchronization for I/O operations

## **NEW: Interactive I/O and String Handling Learnings** 🎯

### Interactive Input with DDT Pattern
**Essential pattern for reliable character input with echo:**

```assembly
/ Input loop using DDT's proven pattern
inloop, cla			/ clear accumulator
        cli			/ clear IO register  
        clf 1			/ clear program flag 1
wait,   szf i 1			/ skip if program flag 1 is zero (indirect)
        jmp wait		/ flag still zero, keep waiting
        tyi			/ flag set, read character
        
        dio temp		/ save character from IO register
        lac temp		/ load character for testing
        tyo			/ echo character back to user
        
        / Check if carriage return (FIODEC 077)
        sub cret		/ subtract carriage return value
        sza			/ skip if zero (character was CR)
        jmp process		/ not CR, process character
        jmp endinput		/ CR found, end input
```

**Key points:**
- Must clear flags (`cla`, `cli`, `clf 1`) before each character wait
- Use `szf i 1` (skip if flag zero) - the TYI instruction automatically clears the flag
- Echo with `tyo` for user feedback
- Test for carriage return (077 in FIODEC) to end input

### FIODEC Character Packing Algorithm
**Pack individual characters into 18-bit words (3 characters per word):**

```assembly
/ Pack character into current word
store,  lac pckwrd		/ load current packed word
        rcl 6s			/ rotate left 6 bits to make room
        dac pckwrd		/ save shifted word
        lac temp		/ load new character
        add pckwrd		/ add to rightmost 6 bits
        dac pckwrd		/ save updated word
        
        lac chrcnt		/ load character counter (3,2,1)
        sub one			/ decrement counter
        dac chrcnt		/ save counter
        sza			/ skip if word complete (counter = 0)
        jmp inloop		/ not complete, continue packing
        
        / Word complete - store and start new word
        lac pckwrd		/ load completed word
        dac i nameptr		/ store at current buffer position
        idx nameptr		/ increment buffer pointer
        law 3			/ reset counter for next word
        dac chrcnt
        cla			/ clear for new word
        dac pckwrd
        jmp inloop		/ continue input
```

### Partial Word Handling for Clean Display
**Critical fix for eliminating unwanted spaces in names:**

```assembly
/ Handle partial word (less than 3 characters) 
partwd, / Pad partial word with carriage returns
        lac chrcnt		/ get remaining empty positions
pad,    sza			/ skip if no padding needed
        jmp dopad		/ need to pad
        jmp donepad		/ padding complete
dopad,  lac pckwrd		/ load current word
        rcl 6s			/ shift left 6 bits
        dac pckwrd		/ save shifted word
        lac cret		/ load carriage return (077)
        add pckwrd		/ add CR to rightmost position
        dac pckwrd		/ save padded word
        lac chrcnt		/ get remaining count
        sub one			/ decrement
        dac chrcnt
        jmp pad			/ continue until padded
donepad,
        lac pckwrd		/ store padded word
        dac i nameptr
        idx nameptr		/ add separate terminator  
        lac cret		/ for clean program halt
        dac i nameptr
        jmp i input		/ return from subroutine
```

**Why this works:**
- Names like "oscar" (5 chars) become: word1="osc", word2="ar"+CR
- Print loop extracts "o","s","c" then "a","r", then hits CR and halts
- No unwanted spaces from unused character positions
- Works for any name length

### Print Loop with Carriage Return Detection
**Modified print loop that stops cleanly on carriage return:**

```assembly
lu2,    lac word
        lio word
        rcl 6s			/ extract next character
        dac word
        
        / Check if character is carriage return
        lio word		/ get character in IO register
        dio temp		/ save character  
        lac temp
        sub cret		/ compare with CR (077)
        sza			/ skip if carriage return
        jmp prtchr		/ not CR, print it
        hlt			/ CR found, halt program cleanly
        
prtchr, tyo			/ print character
        / ... continue normal character loop
```

**Essential insight:** The print loop must check each character value and halt on carriage return, not just rely on memory address comparisons (`sas`).

### Buffer Management Best Practices
```assembly
/ Clear name buffer before use (prevents old data)
        law namebuf		/ load ADDRESS of buffer (not contents!)
        dac nameptr		/ initialize pointer
        
        cla			/ clear buffer contents
        dac namebuf		/ clear word 1
        dac namebuf+1		/ clear word 2  
        dac namebuf+2		/ clear word 3
        dac namebuf+3		/ clear word 4
```

**Critical detail:** Use `law namebuf` (load address) not `lac namebuf` (load contents) when initializing buffer pointers.

# PDP-1 Programming Learnings - Session 2

## FIODEC Paper Tape Encoding & Decoding Tools

### You can use complete FIODEC file conversion tool

**encode_fiodec.py** - ASCII to PDP-1 Paper Tape Converter:
- **FIODEC Character Mapping**: Complete reverse mapping from decode_fiodec.py
- **ASCII Fallback Support**: `*` → `×`, `^` → `↑` for unmappable characters
- **Paper Tape Leader/Trailer**: Configurable null byte padding (50 bytes default)
- **Command Line Options**: `--table` for encoding reference, `--no-leader` for raw content

**decode_fiodec.py** - Existing decoder (confirmed working with parity)

**Bash Wrapper Scripts**: `encode_fiodec` and `decode_fiodec` for standalone CLI use
- **Command Line Options**: installed in /usr/local/bin for PiDP-1 users

### Critical Parity Discovery

**Alphanumeric Paper Tape Parity Rules**:
- **Content Characters**: Must have odd parity (8th hole = bit 7 = 0x80)
- **Leader/Trailer Nulls**: Remain 0x00 (no parity bits on tape feed holes)
- **Parity Calculation**: Count 1-bits in 7-bit FIODEC code, add parity if even

## Advanced PDP-1 I/O Programming Techniques

### IOT Instruction Variants and Completion Pulse Management

**Standard TYO vs Specialized IOT**:
```assembly
tyo             ; Standard: waits for completion pulse
iot 4003        ; Variant: "tyo with nac but no ioh"
```

**IOT 4003 Analysis** (octal breakdown):
- **Device 003**: Typewriter
- **Bit 6 = 1**: "nac" (No AC modification)
- **Bit 5 = 0**: "no ioh" (No Input-Output Halt wait)

### Overlapped I/O Processing Pattern

**Advanced Technique**: Decouple I/O initiation from completion checking:

```assembly
iot 4003        ; Start typewriter (non-blocking)
lac data        ; Do useful computation  
add value       ; while typewriter prints
dac result      ; mechanically...
iot i 0         ; Synchronize using pending completion pulse
```

**Hardware Completion Pulse Mechanism**:
- **Completion Pulse Latch**: Set by device completion, cleared when consumed
- **Persistent State**: Pulse remains available until consumed by IOT with wait
- **Asynchronous Operation**: Allows concurrent processing on single-threaded 1959 hardware

### Key Programming Insights

**Completion Pulse Reuse**:
1. `iot 4003` generates completion pulse but doesn't consume it
2. Subsequent `iot i xxxx` immediately satisfies using pending pulse
3. Enables sophisticated overlapped I/O without race conditions

**Performance Benefits**:
- **Maximum CPU utilization**: Work continues during mechanical I/O
- **Guaranteed synchronization**: Later IOT ensures I/O completion
- **Hardware efficiency**: One completion pulse serves multiple purposes

## NOP Instruction Reference

**NOP (No Operation)**: `760000` octal
- **Execution time**: 5 microseconds
- **Function**: Advances PC, useful for timing delays or placeholders
- **Category**: Operate Group instruction

## Development Tools Created

**Standalone CLI Programs**:
- `encode_fiodec <input.mac> <output.ptx>` - Convert ASCII to paper tape
- `decode_fiodec <input.ptx> <output.mac>` - Convert paper tape to ASCII
- Both include error handling, dependency checking, and proper help messages

**Usage Examples**:
```bash
# Convert assembly source to authentic paper tape format
encode_fiodec program.mac program.pt

# Show FIODEC character encoding table
encode_fiodec --table

# Convert without leader/trailer (raw content only)
encode_fiodec program.mac program.pt --no-leader

# Convert paper tape back to ASCII source
decode_fiodec program.ptx program_decoded.mac
```

## Historical Programming Insight

The PDP-1's completion pulse system represents remarkably sophisticated **interrupt-like behavior** implemented with simple 1959 hardware. The ability to:
- Generate asynchronous completion signals
- Latch completion state persistently  
- Allow software-controlled pulse consumption
- Enable overlapped I/O processing

...demonstrates advanced computer architecture concepts that wouldn't become common until much later systems. This shows the PDP-1 was truly ahead of its time in I/O subsystem design.

