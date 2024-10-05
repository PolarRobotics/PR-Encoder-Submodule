import time
from rp2 import PIO, StateMachine, asm_pio
import rp2
from machine import Pin

@rp2.asm_pio(out_init=(PIO.OUT_LOW), sideset_init=(PIO.OUT_LOW))
def led_blink():
    # nop() # read 0000, keep led off
    # jump("turnon_led") # read 0001, turn led on

    wrap_target() # start here
    label("turnon_led")
    nop() .side(0x0)

    # out(isr, 2) # move 2 bits from OSR to ISR
    # in_(pins, 2) # then 2 bits from pins to ISR

  
    # mov(osr, isr) # Save the state in the OSR, so that we can use ISR for other purposes
    # mov(pc, osr) # jump to the correct state machine action by moving PC

    # # mov(osr, isr) # Save the state in the OSR, so that we can use ISR for other purposes
    wrap() # wrap

sm1 = StateMachine(0, led_blink, freq=2000, sideset_base=Pin(25))
sm1.active(1)
while True:
    print("test")