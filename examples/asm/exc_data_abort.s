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
    ldr r0, =0x09000000
    ldr r1, [r0]
after_abort:
    b after_abort

dabort_handler:
    mov r4, #0xDA
    b dabort_handler

undef_handler:  b undef_handler
swi_handler:    b swi_handler
pabort_handler: b pabort_handler
irq_handler:    b irq_handler
fiq_handler:    b fiq_handler
