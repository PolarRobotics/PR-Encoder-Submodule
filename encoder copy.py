import time
from rp2 import PIO, StateMachine, asm_pio
import rp2
from machine import Pin, I2C
import time
import _thread

# Local
from i2c_responder import I2CResponder

I2C_FREQUENCY = 400000

RESPONDER_I2C_DEVICE_ID = 0
RESPONDER_ADDRESS = 0x41
GPIO_RESPONDER_SDA = 0
GPIO_RESPONDER_SCL = 1

@rp2.asm_pio(set_init=(PIO.IN_HIGH, PIO.IN_HIGH, PIO.IN_HIGH, PIO.IN_HIGH), out_init=(PIO.OUT_HIGH, PIO.OUT_HIGH))
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

    # nop instructions to set instruction count to 32 instructions 
    # (THIS IS NECESSARY FOR THE CODE TO RUN CORRECTLY)
    nop()
    nop()
    nop()
    nop()
    nop()
    #nop()


# Setup the first state machine
sm1 = StateMachine(0, quadrature_encoder, freq = 10000000, in_base=Pin(2), set_base=Pin(2), out_shiftdir=PIO.SHIFT_RIGHT)
sm1.exec("set(y, 0)")              # Start with a count of 0
sm1.active(1)                      # Start the state machince

# Setup the second state machine
sm2 = StateMachine(1, quadrature_encoder, freq = 10000000, in_base = Pin(4), set_base=Pin(4), out_shiftdir=PIO.SHIFT_RIGHT)
sm2.exec("set(y, 0)")              # Start with a count of 0
sm2.active(1)                      # Start the state machine

# Used to convert the unsigned count to a signed 32-bit number
def to_signed_32bit(n):
    n = n & 0xFFFFFFFF   # Limit to 32 bits
    if n >= 0x80000000:  # Check if it's negative in 32-bit signed form
        n -= 0x100000000
    return n

def format_hex(_object):
    """Format a value or list of values as 2 digit hex."""
    try:
        values_hex = [to_hex(value) for value in _object]
        return '[{}]'.format(', '.join(values_hex))
    except TypeError:
        # The object is a single value
        return to_hex(_object)


def to_hex(value):
    return '0x{:02X}'.format(value)


# Uses the encoder count to calculate the speed in rpm's
def calcSpeed(curr, prev, prev_time):
    omega = 0                       # Set omega to 0
    current_time = time.time_ns()   # Get current time

    # Calculate omega using current and previous encoder counts, and current and previous time
    omega = float((curr - prev)) / float((current_time - prev_time))

    # After calculation, set previous values to the current for the next calculation
    prev_time = current_time
    prev = curr

    omega = omega * 15000000        # Multiply omega by 60 / PPR * 1 Billion (nanoseconds to seconds)
    return prev, omega, prev_time   # Return previous values to be passed through calcSpeed along with the speed

# Instantiate variables for previous count and time
Enc1Prev = 0
Enc2Prev = 0
Enc1Prev_time = 0
Enc2Prev_time = 0

# Main loop
while True:
    Enc1Count = to_signed_32bit(sm1.get())                          # Convert Encoder 1 count to signed
    #Enc2Count = to_signed_32bit(sm2.get())                          # Convert Encoder 2 count to signed
    Enc1Prev, Enc1Speed, Enc1Prev_time = calcSpeed(Enc1Count, Enc1Prev, Enc1Prev_time)  # Calculate the speed from Encoder 1
    #Enc2Prev, Enc2Speed, Enc2Prev_time = calcSpeed(Enc2Count, Enc2Prev, Enc2Prev_time)  # Calcutate the speed from Encoder 2

    # Print out data
    # print("-------------------------")
    # print("Encoder 1 Count: %d      " % (Enc1Count))
    # print("Encoder 2 Count: %d\n" % (Enc2Count))
    # print("Encoder 1 Speed: %f      " % (Enc1Speed))
    # print("Encoder 2 Speed: %f" % (Enc2Speed))
    # print("-------------------------\n")
    # -----------------
    # Initialize Responder and Controller
    # -----------------
    i2c_responder = I2CResponder(
        RESPONDER_I2C_DEVICE_ID, sda_gpio=GPIO_RESPONDER_SDA, scl_gpio=GPIO_RESPONDER_SCL, responder_address=RESPONDER_ADDRESS
    )
    #print('Testing I2CResponder v' + i2c_responder.VERSION)


    # -----------------
    # Demonstrate I2C READ
    # -----------------
    # NOTE: We want the Controller to initiate an I2C READ, but the Responder implementation
    #   is polled.  As soon as we execute i2c_controller.readfrom() we will block
    #   until the I2C bus supplies the requested data.  But we need to have executional
    #   control so that we can poll i2c_responder.read_is_pending() and then supply the
    #   requested data.  To circumvent the deadlock, we will briefly launch a thread on the
    #   second Pico core, and THAT thread will execute the .readfrom().  That thread will block
    #   while this thread polls, then supplies the requested data.
    # -----------------
    # thread_lock = _thread.allocate_lock()
    # _thread.start_new_thread(thread_i2c_controller_read, (i2c_controller, thread_lock))
    buffer_out = bytearray([Enc1Count, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    
    # print("Waiting for data to recieve...")
    # while not i2c_responder.write_data_is_available():
    #     pass
    # data = i2c_responder.get_write_data(max_size=1)
    # for i, value in enumerate(data):
    #     READBUFFER[i] = value
    #     print('Controller: Received I2C READ data: ' + format_hex(READBUFFER))
    
    print("Waiting for write instruction...")
        # We will loop here (polling) until the Controller (running on its own thread) issues an
        # I2C READ.
    if(i2c_responder.read_is_pending()):    
        for value in buffer_out:
            i2c_responder.put_read_data(value)
        # with thread_lock:
            print('   Responder: Transmitted I2C READ data: ' + format_hex(buffer_out))
        
    #time.sleep_ms(100)
    