.syntax unified
.cpu arm7tdmi
.arm
.global _start

_start:
    swi #0x11
after_swi:
    b after_swi
