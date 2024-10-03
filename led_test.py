import time
from rp2 import PIO, StateMachine, asm_pio
import rp2
from machine import Pin

@rp2.asm_pio(set_init=(PIO.IN_HIGH, PIO.IN_HIGH), out_init=(PIO.OUT_HIGH, PIO.OUT_HIGH))
def led_blink():
    wrap_target() # start here

    out(isr, 2) # move 2 bits from OSR to ISR
    in_(pins, 2) # then 2 bits from pins to ISR

    mov(osr, isr) # Save the state in the OSR, so that we can use ISR for other purposes
    wrap() # wrap
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()

sm1 = StateMachine(0, led_blink, freq=2000, set_base=Pin(1))
sm1.active(1)
while True:
    sm1.put(1 << 3)
