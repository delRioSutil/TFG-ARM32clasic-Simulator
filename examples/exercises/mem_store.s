.syntax unified
.cpu arm7tdmi
.arm
.global _start

_start:
    ldr r0, =value
    ldr r1, =0x12345678
    str r1, [r0]
end:
    b end

.align 2
value:
    .word 0
