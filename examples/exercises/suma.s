.syntax unified
.cpu arm7tdmi
.arm
.global _start

_start:
    mov r0, #1
    mov r1, #2
    add r2, r0, r1

end:
    b end
