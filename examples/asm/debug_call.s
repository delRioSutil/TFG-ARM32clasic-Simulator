.syntax unified
.cpu arm7tdmi
.arm
.global _start
.global main

_start:
    b main

main:
    mov r0, #1
    bl add_two
after_call:
    mov r2, r0
hang:
    b hang

add_two:
    add r0, r0, #2
    mov pc, lr
