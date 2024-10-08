import time
from rp2 import PIO, StateMachine, asm_pio
import rp2
from machine import Pin

@rp2.asm_pio(set_init=(PIO.IN_HIGH, PIO.IN_HIGH), out_init=(PIO.OUT_HIGH, PIO.OUT_HIGH), sideset_init=(PIO.OUT_LOW))
def led_blink():
    jmp("on") # read 0000
    jmp("off") # read 0001
    jmp("off") #read 0010
    jmp("off") #read 0011
    jmp("off") #read 0100
    jmp("off") #read 0101
    jmp("off") #read 0110

    jmp("off") #read 0111
    #jmp("on") #read 0111

    jmp("off") #read 1000
    jmp("off") #read 1001
    jmp("off") #read 1010

    jmp("off") #read 1011
    #jmp("on")#read 1011

    jmp("off") #read 1100
    jmp("off") #read 1101
    jmp("off") #read 1110
    jmp("off") #read 1111
    
    wrap_target() # start here 

    label("on")
    nop() .side(0x1)
    out(isr, 2) # move 2 bits from OSR to ISR
    in_(pins, 2) # then 2 bits from pins to ISR
    mov(osr, isr) # Save the state in the OSR, so that we can use ISR for other purposes
    push(noblock)
    mov(pc, osr) # jmp to the correct state machine action by moving PC

    label("off")
    nop() .side(0x0)
    out(isr, 2) # move 2 bits from OSR to ISR
    in_(pins, 2) # then 2 bits from pins to ISR
    mov(osr, isr) # Save the state in the OSR, so that we can use ISR for other purposes
    push(noblock)
    mov(pc, osr) # jmp to the correct state machine action by moving PC

    # to get to 32 instructions
    nop()
    nop()
    nop()    
    nop()
    #nop()
    #nop()
    #nop()
    #nop() 
    #nop()
    #nop()
    #nop()
    #nop()
    
    wrap() # wrap

sm1 = StateMachine(0, led_blink, freq=2000, set_base=Pin(0), out_shiftdir=PIO.SHIFT_RIGHT, sideset_base=Pin(25))
sm1.active(1)
while True:
    print("PIN Values: %x" % (sm1.get()))