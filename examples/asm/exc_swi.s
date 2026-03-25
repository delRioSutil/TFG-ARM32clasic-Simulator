.syntax unified
.cpu arm7tdmi
.arm
.global _start

.section .text

/* Vector table at 0x00000000 */
vectors:
    b _start          /* 0x00 Reset */
    b undef_handler   /* 0x04 Undefined */
    b swi_handler     /* 0x08 SWI */
    b pabort_handler  /* 0x0C Prefetch abort */
    b dabort_handler  /* 0x10 Data abort */
    b .               /* 0x14 Reserved */
    b irq_handler     /* 0x18 IRQ */
    b fiq_handler     /* 0x1C FIQ */

_start:
    mov r0, #1
    swi #0x11         /* dispara SWI */
after_swi:
    mov r2, #0x55
hang:
    b hang

undef_handler:   b undef_handler
pabort_handler:  b pabort_handler
dabort_handler:  b dabort_handler
irq_handler:     b irq_handler
fiq_handler:     b fiq_handler

swi_handler:
    mov r1, #0x42
    b swi_handler
