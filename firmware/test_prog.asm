;Header
.MEMORYMAP
SLOTSIZE $8000
DEFAULTSLOT 1
SLOT 0 $0 SIZE $2000 ; BSS
SLOT 1 $2000 SIZE $2000 ; Init RAM=>ROM=>I/O=>IPL
.ENDME

.ROMBANKSIZE $2000
.ROMBANKS 1
.EMPTYFILL $FF


;Defines
.DEFINE LED_BASE $FE00


;Macros
.MACRO NOPMONSTER
       .REPT 100        ; evil...
       NOP
       .ENDR
.ENDM


;I/O
;Bug- Don't try using .DB in .STRUCT
;Workaround- DSB 0
.STRUCT LED_IO
CTRL DB
.ENDST

.ENUM LED_BASE
LEDS INSTANCEOF LED_IO
.ENDE


; .RAMSECTION "BSS" SLOT 0 FORCE 
;test_prog.asm:17: DIRECTIVE_ERROR: Unexpected symbol "test:".
;test_prog.asm:17: ERROR: Couldn't parse "test:".
.RAMSECTION "BSS" SLOT 0
RAB: .DW
RA: DB
RB: DB
RCD: .DW
RC: DB
RD: DB
REF: .DW
RE: DB
RF: DB
RGH: .DW
RG: DB
RH: DB
RSP: .DW
RSL: DB
RSH: DB

.ENDS


.BANK 0
.ORG $0
;.ORGA $2000
.SECTION "DATA" FREE
;Banner: "6502 Test Program (C) 2015"
Banner: .DB "6502 Test Program (C) 2015"

.ENDS


.SECTION "TEXT" SEMIFREE
EmptyHandler:
	RTI

Start:
    LDX #$FF
    TXS
    LDX #$00
    LDY #$00
    LDA #$00
Again:
    STA LEDS.CTRL ; Toggle LEDs
;    STA RA
;    LDA RA
;    EOR #$FF
;    JMP Again
;Loop: JMP Loop
    LDY #$FF
Wait1: ; Loop 65535 times
    LDX #$FF
Wait2:
    NOPMONSTER
    DEX
    BNE Wait2
    DEY
    BEQ Done
    JMP Wait1
Done:
    EOR #$FF    
    JMP Again
.ENDS


; Address decoding is incomplete. Page 0xFF => 0x3F
.ORGA $3FFA
.SECTION "Vectors" FORCE
NMI: .DW EmptyHandler
RESET: .DW Start
IRQBRK: .DW EmptyHandler
.ENDS
