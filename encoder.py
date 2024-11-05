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
    jmp("update")    # read 0000
    jmp("decrement") # read 0001
    jmp("increment") # read 0010
    jmp("update")    # read 0011

# ; 01 state
    jmp("increment") # read 0100
    jmp("update")    # read 0101
    jmp("update")    # read 0110
    jmp("decrement") # read 0111

# ; 10 state
    jmp("decrement") # read 1000 ( Seems to work for decrementing 9/23 )
    jmp("update")    # read 1001
    jmp("update")    # read 1010
    jmp("increment") # read 1011

# ; to reduce code size, the last 2 states are implemented in place and become the
# ; target for the other jumps

# ; 11 state
    jmp("update")    # read 1100
    jmp("increment") # read 1101
    jmp("decrement") # read 1110    
    jmp("update")    # read 1111


    label("decrement")
    jmp(y_dec, "update")

    
# this is where the main loop starts
    wrap_target()
    
    #set(y,0)

    label("update")
    mov(isr, y)
    push(noblock)

    label("sample_pins")

# Move 2 bits from OSR to ISR, then 2 bits from pins to ISR 
    out(isr, 2)
    in_(pins, 2)

# Save the state in the OSR, so that we can use ISR for other purposes
    mov(osr, isr)

# jump to the correct state machine action
    mov(pc, osr)    # Was isr, experimenting with osr

# There is no increment operator, so we have to 
# negate, decrement, and then negate again.
    label("increment")
    mov(y, invert(y))
    jmp(y_dec, "increment_cont")

    label("increment_cont")
    mov(y, invert(y))
    jmp("update")
    wrap()
    nop()
    nop()
    nop()
    nop()
    nop()
    #nop()


# Setup the first state machine
sm1 = StateMachine(0, quadrature_encoder, freq = 10000000, set_base=Pin(0), out_shiftdir=PIO.SHIFT_RIGHT)
sm1.exec("mov(y,invert(null))")    # Start with a count of 0
sm1.active(1)           # Start the state machince

# Used to convert the unsigned count to a signed 32-bit number
def to_signed_32bit(n):
    n = n & 0xFFFFFFFF  # Limit to 32 bits
    if n >= 0x80000000:  # Check if it's negative in 32-bit signed form
        n -= 0x100000000
    return n

# Uses the encoder count to calculate the speed in rpm's
def calcSpeed(curr, prev, prev_time):
    rollover_threshold = 10000  # Is not used for now, set to an arbitrary number so it is unused 10/30/24
    rollover = 4000 # Encoder Resolution * 4
    omega = 0
    current_time = time.time_ns()
    if abs(curr - prev) >= rollover_threshold:
        if (curr - rollover_threshold) > 0:
            omega = (float((curr - rollover) - prev) / float((current_time-prev_time)))
            print("Condition 1\n")
        else:
            omega = (float((curr + rollover) - prev) / float((current_time-prev_time)))
            print("Condition 2\n")
    else: 
        omega = float((curr - prev)) / float((current_time - prev_time))
        print("Condition 3\n")
    prev_time = current_time
    prev = curr
    omega = omega * 15000000        # Multiply omega by 60 / PPR * 1 Billion (nanoseconds to seconds)
    return prev, omega, prev_time
prev = 0
prev_time = 0

# Main loop
while True:
    count = to_signed_32bit(sm1.get())                          # Convert to signed
    prev, speed, prev_time = calcSpeed(count, prev, prev_time)  # Calculate the speed
    print("Encoder Count: %d\n" % (count))
    print("Speed: %f\n" % (speed))
    time.sleep_ms(50)