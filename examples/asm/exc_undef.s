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
    .word 0xE7F000F0
after_undef:
    b after_undef

undef_handler:
    mov r4, #0x44
    b undef_handler

swi_handler:    b swi_handler
pabort_handler: b pabort_handler
dabort_handler: b dabort_handler
irq_handler:    b irq_handler
fiq_handler:    b fiq_handler
