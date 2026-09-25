---
book: "8051 Microcontroller Notes"
genre: "Nonfiction"
bookline: "Embedded-systems study notes on the 8051 microcontroller: architecture, registers, memory map, addressing modes, timers, interrupts, serial communication, and real-world interfacing."
---
--- card
id: 520
title: "The integrated 8051: one 8-bit machine that is CPU, memory, timers, UART, and ports at once"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "source_locator", "ripped_at", "intents"]
type: "concept"
source_locator: "8051 FAMILY"
ripped_at: "2026-09-25"
intents: ["see clearly", "make a decision"]
---
## Steal

The original 8051 is an 8-bit processor with 128 bytes of RAM, 4 KB of on-chip ROM, two timers, one serial port, and four 8-bit I/O ports — a whole control system, not just a CPU, squeezed into one chip with its peripherals permanently wired in.

## Why it matters

The notes never treat the 8051 as a lone processor; every section (ports, timers, serial, interrupts) is about how the core cooperates with its on-chip peripherals, so the useful unit of study is the whole chip's data paths, not any one instruction.

## Use when

Designing or debugging any microcontroller system — decide what to integrate versus what to add externally, and how much work a constrained core can offload to its on-chip peripherals.

--- card
id: 521
title: "The 8051 memory map: four register banks, 128 bit-addressable bits, and SFRs at 80H-FFH"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "source_locator", "ripped_at", "intents"]
type: "mechanism"
source_locator: "SFR Registers and Their Addresses"
ripped_at: "2026-09-25"
intents: ["build something", "see clearly"]
---
## Steal

Internal RAM is stratified by function: 00H-1FH holds four banks of eight registers selected by RS1/RS0 (PSW.4/PSW.3), 20H-2FH gives 128 individually addressable bits, 30H-7FH is plain scratchpad — and the special-function registers sit in a separate control plane at 80H-FFH, addressable by name or number. The stack pointer starts at 07H, so the first push lands at 08H.

## Why it matters

On the 8051, where data lives determines how you touch it — register bits, bit RAM, and SFRs each have their own access rules — so the memory map is not background detail, it is the instruction set's context.

## Use when

Writing or debugging 8051 code — choose register banks vs scratchpad deliberately, guard the stack against the register area, and reach control hardware only through its SFR addresses.

--- card
id: 522
title: "Five addressing modes, and why register-indirect is restricted to R0 and R1"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "source_locator", "ripped_at", "intents"]
type: "mechanism"
source_locator: "ADDRESSING MODES"
ripped_at: "2026-09-25"
intents: ["build something", "name the mechanism"]
---
## Steal

The 8051 offers five addressing modes — immediate, register, direct, register-indirect, indexed — but register-indirect into internal RAM is limited to R0 and R1, and code-space table reads use MOVC A,@A+DPTR while external data uses MOVX; the chip keeps a 64 KB code space and a separate 64 KB external data space, so the instruction, not just the address, chooses which memory you touch.

## Why it matters

This is the notes' recurring lesson that addressing is a hardware data path, not just syntax: the same DPTR can reach ROM via MOVC or external RAM via MOVX, and that distinction is how lookup tables, external memory, and code fetches stay separate on a 16-bit address bus.

## Use when

Laying out data on an 8051 — put constant tables in code space for MOVC, variables in external data space for MOVX, and keep pointer discipline to R0/R1 for internal indirect access.

--- card
id: 523
title: "Read-modify-write instructions read the port latch, not the pin"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "source_locator", "ripped_at", "intents"]
type: "mechanism"
source_locator: "Reading Latch Instructions Reading a latch (Read-Modify-Write)"
ripped_at: "2026-09-25"
intents: ["see clearly", "build something"]
---
## Steal

Some instructions read the external pin state, but read-modify-write instructions read the internal port latch, modify it, and write it back — so a bit toggled this way reflects what the port was last driven to, not what is happening on the pin. Port 0 is open-drain and needs external 10K pull-ups; it also multiplexes address/data (AD0-AD7), while P2 carries the high address byte (A8-A15) and P3 pins double as RxD/TxD, INT0/INT1, T0/T1, WR, and RD.

## Why it matters

This latch-vs-pin split is the classic source of 8051 port bugs — toggling a bit can resurrect a stale value — and the notes treat the ports' alternate functions as the price of the chip's integration: every pin does two jobs.

## Use when

Toggling 8051 port bits or driving external buses — know whether your instruction reads the latch or the pin, add the pull-ups on P0, and account for which pins are stolen by timers, interrupts, or memory access.

--- card
id: 524
title: "The timer as an overflow machine: TMOD splits control, THx/TLx count up, TFx signals the roll-over"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "source_locator", "ripped_at", "intents"]
type: "mechanism"
source_locator: "TIMERS — TMOD Register"
ripped_at: "2026-09-25"
intents: ["build something", "name the mechanism"]
---
## Steal

One machine cycle is 12 oscillator periods (1.085 us at 11.0592 MHz), and that heartbeat feeds Timer 0 and Timer 1. The TMOD register splits control between them — the lower nibble configures Timer 0, the upper nibble Timer 1 — each timer counts in THx/TLx, raises the TFx flag on overflow, and is started or stopped with TRx. Mode 1 is a 16-bit counter that must be reloaded by hand after every overflow; Mode 2 is 8-bit auto-reload, where TH holds the reload value and TL counts and silently reloads on overflow.

## Why it matters

The notes hammer one insight: precision timing on a tiny chip is not about speed, it is about the reload discipline — mode choice decides whether you pay a reload cost per tick or let the hardware do it, which is exactly how the notes generate baud rates and square waves.

## Use when

Generating a delay, square wave, or baud clock on the 8051 — pick the mode whose reload discipline fits the job, then compute the TH/TL values from the 1.085 us heartbeat.

--- card
id: 525
title: "The UART as a framing machine: start bit, 8 data bits, stop bit, with software-cleared TI and RI"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "source_locator", "ripped_at", "intents"]
type: "mechanism"
source_locator: "SERIAL PORT"
ripped_at: "2026-09-25"
intents: ["build something", "see clearly"]
---
## Steal

In the 8-bit asynchronous mode, every byte is framed with one start bit, eight data bits, and one stop bit. SBUF is the byte register; SCON controls the mode; TI fires when the stop bit has been transmitted and RI fires when a full byte lands — and the CPU must clear both flags itself, or the handshake stalls. Baud comes from Timer 1 running in mode 2, so at 11.0592 MHz the reload values TH1 = FDH, FAH, F4H, and E8H give 9600, 4800, 2400, and 1200 baud respectively.

## Why it matters

The notes present serial communication as three cooperating mechanisms — framing, flags, and a timer-derived clock — and the load-bearing detail is that the CPU, not the hardware, owns TI/RI; forgetting to clear them is a silent deadlock.

## Use when

Bringing up an 8051 UART link — verify the framing in SCON, confirm Timer 1 mode 2 with the right TH1 reload, and always clear TI/RI in the handler before doing anything else.

--- card
id: 526
title: "Interrupts on the 8051: a fixed vector table, EA as a master switch, IP priority, and RETI clearing the in-service flag"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "source_locator", "ripped_at", "intents"]
type: "mechanism"
source_locator: "INTERRUPTS — Six Interrupts in 8051"
ripped_at: "2026-09-25"
intents: ["name the mechanism", "build something"]
---
## Steal

Six interrupts live at fixed ROM addresses — Reset 0000H, INT0 0003H, TF0 000BH, INT1 0013H, TF1 001BH, serial 0023H. On an interrupt the CPU finishes the current instruction, pushes the PC, and jumps; the ISR ends with RETI, which restores the PC and clears the interrupt-in-service flag so the pin can fire again. The IE register masks each interrupt individually but nothing works unless EA (IE.7) is set, and the IP register can reorder the default priority (INT0, TF0, INT1, TF1, serial).

## Why it matters

The notes' core contrast is polling versus interrupts — polling burns the CPU watching devices that need nothing, while interrupts let the chip do real work until TF or a pin demands attention — and the whole system hinges on two one-bit disciplines: EA as the master switch and RETI's hidden flag-clear.

## Use when

Designing interrupt-driven 8051 firmware — set EA plus the individual IE bit, place the ISR at its vector address, and end with RETI (never RET) so the interrupt can re-arm.

--- card
id: 527
title: "Memory-mapped I/O and address decoding: the 74LS138 turns address bits into chip selects, and aliases are the price of partial decoding"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "source_locator", "ripped_at", "intents"]
type: "mechanism"
source_locator: "MEMORY ADDRESS DECODING — Using 74LS138 3-8 Decoder"
ripped_at: "2026-09-25"
intents: ["build something", "make a decision"]
---
## Steal

The 8051 talks to peripherals like memory: the 74LS138 3-to-8 decoder turns three address lines (A, B, C) into eight active-low outputs, each wired to a chip's CS pin, so one decoder selects eight memory blocks. An I/O chip like the 8255 is wired to the bus as if it were RAM and driven with MOVX; its A1/A0 lines pick Port A, Port B, Port C, or the control register, and a control word configures each port as input or output (with a bit-set/reset mode that can flip single Port C bits). Decoding only part of the address creates aliases — many addresses reaching the same physical port — which must be documented.

## Why it matters

This is the notes' bridge from chip internals to real hardware: the CPU's address bus becomes a selection mechanism, and the engineering judgment is what to decode fully (clean addresses) versus partially (cheap but aliased).

## Use when

Expanding an 8051 system with external memory or I/O chips — decode enough address lines for clean selects, document every alias, and configure peripherals with a control word before touching their data ports.
