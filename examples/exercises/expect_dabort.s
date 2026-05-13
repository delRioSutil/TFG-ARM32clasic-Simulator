.syntax unified
.cpu arm7tdmi
.arm
.global _start

_start:
    ldr r0, =0x09000000
    ldr r1, [r0]
after_abort:
    b after_abort
