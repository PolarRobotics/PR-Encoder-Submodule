import time
from rp2 import PIO, StateMachine, asm_pio
import rp2
from machine import Pin

@rp2.asm_pio(set_init=(PIO.IN_HIGH, PIO.IN_HIGH), out_init=(PIO.OUT_HIGH, PIO.OUT_HIGH))
def quadrature_encoder():

# Binary value for each jump are the memory addresses that the instructions are located at.
# i.e. 0000 is the first address in memory

# *
# Need to force the program to start at address 0, using nop() until there are 32 instructions :(
# * 
#     ; 00 state
     jmp('update')    # read 0000
     jmp('decrement') # read 0001
     jmp('increment') # read 0010
     jmp('update')    # read 0011

# ; 01 state
     jmp('increment') # read 0100
     jmp('update')    # read 0101
     jmp('update')    # read 0110
     jmp('decrement') # read 0111

# ; 10 state
     jmp('decrement') # read 1000
     jmp('update')    # read 1001
     jmp('update')    # read 1010
     jmp('increment') # read 1011

# ; to reduce code size, the last 2 states are implemented in place and become the
# ; target for the other jumps

# ; 11 state
     jmp('update')    # read 1100
     jmp('increment') # read 1101


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


sm1 = StateMachine(0, quadrature_encoder, freq=2000, set_base=Pin(1), out_base=Pin(1))

sm1.irq(None, 1)