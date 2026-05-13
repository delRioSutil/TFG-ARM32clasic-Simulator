.syntax unified
.cpu arm7tdmi
.arm
.global _start
.global main

_start:
    b main
    b undef_handler
    b swi_handler
    b pabort_handler
    b dabort_handler
    b .
    b irq_handler
    b fiq_handler

main:
    ldr pc, =0x09000000
after_abort:
    b after_abort

pabort_handler:
    mov r4, #0x0C
    b pabort_handler

undef_handler:  b undef_handler
swi_handler:    b swi_handler
dabort_handler: b dabort_handler
irq_handler:    b irq_handler
fiq_handler:    b fiq_handler
