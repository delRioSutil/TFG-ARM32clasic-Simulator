.syntax unified
.cpu arm7tdmi
.arm
.global _start
.global main

_start:
vectors:
    b main
    b undef_handler
    b swi_handler
    b pabort_handler
    b dabort_handler
    b .
    b irq_handler
    b fiq_handler

main:
    mov r0, #1
    swi #0x11
after_swi:
    mov r2, r1
hang:
    b hang

undef_handler:   b undef_handler
pabort_handler:  b pabort_handler
dabort_handler:  b dabort_handler
irq_handler:     b irq_handler
fiq_handler:     b fiq_handler

swi_handler:
    mov r1, #0x42
    movs pc, lr
