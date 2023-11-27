import time
import rp2
from machine import Pin

# Assembly Code for the PIO Controller
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def flash():
    wrap_target()
    set(pins, 1)    [31]
    nop()           [31]
    nop()           [31]
    nop()           [31]
    nop()           [31]
    set(pins, 0)    [31]
    nop()           [31]
    nop()           [31]
    nop()           [31]
    nop()           [31]
    wrap()

#Initalize State Machine
sm = rp2.StateMachine(0, flash, freq=2000, set_base=Pin(25))

# Activate state machine, run for three seconds, then stop
sm.active(1)
time.sleep(3)
sm.active(0)