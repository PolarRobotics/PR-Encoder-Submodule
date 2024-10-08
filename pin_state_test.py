import time
from rp2 import PIO, StateMachine, asm_pio
import rp2
from machine import Pin

@rp2.asm_pio(set_init=(PIO.IN_HIGH, PIO.IN_HIGH), out_init=(PIO.OUT_HIGH, PIO.OUT_HIGH))
def read_pins():
    wrap_target()
    out(isr, 2) # move 2 bits from OSR to ISR
    in_(pins, 2) # then 2 bits from pins to ISR
    mov(osr, isr) # Save the state in the OSR, so that we can use ISR for other purposes
    push(noblock)
    wrap()


sm1 = StateMachine(0, read_pins, freq=2000, set_base=Pin(0), out_shiftdir=PIO.SHIFT_RIGHT, )
sm1.active(1)
while True:
    # y_value = sm1.get()
    # print((y_value))
    
    print("PIN Values: %x" % (sm1.get()))

    time.sleep_ms(50)

    #sm1.irq(None, 1)