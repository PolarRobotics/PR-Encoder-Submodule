import time
import rp2
from machine import Pin

@rp2.asm_pio(set_init=(PIO.IN_HIGH, PIO.IN_HIGH))
def quadrature_encoder():

# NEED TO LOOK AT LOGIC FOR THIS CODE
#     ; 00 state
#     JMP update    ; read 00
#     JMP decrement ; read 01
#     JMP increment ; read 10
#     JMP update    ; read 11

# ; 01 state
#     JMP increment ; read 00
#     JMP update    ; read 01
#     JMP update    ; read 10
#     JMP decrement ; read 11

# ; 10 state
#     JMP decrement ; read 00
#     JMP update    ; read 01
#     JMP update    ; read 10
#     JMP increment ; read 11

# ; to reduce code size, the last 2 states are implemented in place and become the
# ; target for the other jumps

# ; 11 state
#     JMP update    ; read 00
#     JMP increment ; read 01


    label("decrement")
    jmp(y_dec, update)
    
# this is where the main loop starts
    wrap_target()

    label("update")
    mov(isr, y)
    push(noblock)

    label("sample_pins")
# Move 2 bits from OSR to ISR, then from ISR to pins
    out(isr, 2)
    in_(pins, 2)

# Save the state in the OSR, so that we can use ISR for other purposes
    mov(osr, isr)

# jump to the correct state machine action
    mov(pc, isr)

# There is no increment operator, so we have to 
# negate, decrement, and then negate again.
    label("increment")
    mov(y, ~y)
    jmp(y_dec, increment_cont)

    label("increment_cont")
    mov(y, ~y)
    wrap()


