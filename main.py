import time
import rp2
from rp2 import PIO, StateMachine, asm_pio
from machine import Pin, I2C, mem32


led = Pin("LED", Pin.OUT)
led.toggle()

class I2CResponder:
    """Implementation of a (polled) Raspberry Pico I2C Responder.

    NOTE: This module uses I2C Controller/Responder nomenclature per
          https://www.eetimes.com/its-time-for-ieee-to-retire-master-slave/

    I2C Responder support is not yet present in Pico micropython (as of MicroPython v1.14).

    This class implements a polled I2C responder by accessing the Pico registers directly.
    The implementation is largely built upon the work of danjperron as posted in:
        https://www.raspberrypi.org/forums/viewtopic.php?f=146&t=302978&sid=164b1038e60b43a22d1af6b6ba69f6ae

    Returns:
        [type]: [description]
    """
    VERSION = "1.0.1"

    # Register base addresses
    I2C0_BASE = 0x40044000
    I2C1_BASE = 0x40048000
    IO_BANK0_BASE = 0x40014000

    # Register access method control flags
    REG_ACCESS_METHOD_RW = 0x0000
    REG_ACCESS_METHOD_XOR = 0x1000
    REG_ACCESS_METHOD_SET = 0x2000
    REG_ACCESS_METHOD_CLR = 0x3000

    # Register address offsets
    IC_CON = 0
    IC_TAR = 4
    IC_SAR = 8
    IC_DATA_CMD = 0x10
    IC_RAW_INTR_STAT = 0x34
    IC_RX_TL = 0x38
    IC_TX_TL = 0x3C
    IC_CLR_INTR = 0x40
    IC_CLR_RD_REQ = 0x50
    IC_CLR_TX_ABRT = 0x54
    IC_ENABLE = 0x6C
    IC_STATUS = 0x70

    # GPIO Register block size (i.e.) per GPIO
    GPIO_REGISTER_BLOCK_SIZE = 8

    # GPIO Register offsets within a GPIO Block
    GPIOxCTRL = 0x04

    # Register bit definitions
    IC_STATUS__RFNE = 0x08  # Receive FIFO Not Empty
    IC_ENABLE__ENABLE = 0x01
    IC_SAR__IC_SAR = 0x1FF  # Responder address
    IC_CLR_TX_ABRT__CLR_TX_ABRT = 0x01
    IC_RAW_INTR_STAT__RD_REQ = 0x20
    IC_CON__CONTROLLER_MODE = 0x01
    IC_CON__IC_10BITADDR_RESPONDER = 0x08
    IC_CON__IC_RESPONDER_DISABLE = 0x40
    GPIOxCTRL__FUNCSEL = 0x1F
    GPIOxCTRL__FUNCSEL__I2C = 3

    def write_reg(self, register_offset, data, method=0):
        """Write Pico register."""
        mem32[self.i2c_base | method | register_offset] = data

    def set_reg(self, register_offset, data):
        """Set bits in Pico register."""
        self.write_reg(register_offset, data, method=self.REG_ACCESS_METHOD_SET)

    def clr_reg(self, register_offset, data):
        """Clear bits in Pico register."""
        self.write_reg(register_offset, data, method=self.REG_ACCESS_METHOD_CLR)

    def __init__(self, i2c_device_id=0, sda_gpio=0, scl_gpio=1, responder_address=0x41):
        """Initialize.

        Args:
            i2c_device_id (int, optional): The internal Pico I2C device to use (0 or 1).
            sda_gpio (int, optional): The gpio number of the pin to use for SDA.
            scl_gpio (int, optional): The gpio number of the pin to use for SCL.
            responder_address (int, optional): The I2C address to assign to this Responder.
        """
        self.scl_gpio = scl_gpio
        self.sda_gpio = sda_gpio
        self.responder_address = responder_address
        self.i2c_device_id = i2c_device_id
        self.i2c_base = self.I2C0_BASE if i2c_device_id == 0 else self.I2C1_BASE
        # Disable I2C engine while initializing it
        self.clr_reg(self.IC_ENABLE, self.IC_ENABLE__ENABLE)
        # Clear Responder address bits
        self.clr_reg(self.IC_SAR, self.IC_SAR__IC_SAR)
        # Set Responder address
        self.set_reg(self.IC_SAR, self.responder_address & self.IC_SAR__IC_SAR)
        # Clear 10 Bit addressing bit (i.e. enable 7 bit addressing)
        # Clear CONTROLLER bit (i.e. we are a Responder)
        # Clear RESPONDER_DISABLE bit (i.e. we are a Responder)
        self.clr_reg(
            self.IC_CON,
            (
                self.IC_CON__CONTROLLER_MODE
                | self.IC_CON__IC_10BITADDR_RESPONDER
                | self.IC_CON__IC_RESPONDER_DISABLE
            ),
        )
        # Configure SDA PIN to select "I2C" function
        mem32[
            self.IO_BANK0_BASE
            | self.REG_ACCESS_METHOD_CLR
            | (self.GPIOxCTRL + self.GPIO_REGISTER_BLOCK_SIZE * self.sda_gpio)
        ] = self.GPIOxCTRL__FUNCSEL
        mem32[
            self.IO_BANK0_BASE
            | self.REG_ACCESS_METHOD_SET
            | (self.GPIOxCTRL + self.GPIO_REGISTER_BLOCK_SIZE * self.sda_gpio)
        ] = self.GPIOxCTRL__FUNCSEL__I2C
        # Configure SCL PIN to select "I2C" function
        mem32[
            self.IO_BANK0_BASE
            | self.REG_ACCESS_METHOD_CLR
            | (self.GPIOxCTRL + self.GPIO_REGISTER_BLOCK_SIZE * self.scl_gpio)
        ] = self.GPIOxCTRL__FUNCSEL
        mem32[
            self.IO_BANK0_BASE
            | self.REG_ACCESS_METHOD_SET
            | (self.GPIOxCTRL + self.GPIO_REGISTER_BLOCK_SIZE * self.scl_gpio)
        ] = self.GPIOxCTRL__FUNCSEL__I2C
        # Enable i2c engine
        self.set_reg(self.IC_ENABLE, self.IC_ENABLE__ENABLE)

    def read_is_pending(self):
        """Return True if the Controller has issued an I2C READ command.

        If this function returns True then the Controller has issued an
        I2C READ, which means that its I2C engine is currently blocking
        waiting for us to respond with the requested I2C READ data.
        """
        status = mem32[self.i2c_base | self.IC_RAW_INTR_STAT] & self.IC_RAW_INTR_STAT__RD_REQ
        return bool(status)

    def put_read_data(self, data):
        """Issue requested I2C READ data to the requesting Controller.

        This function should be called to return the requested I2C READ
        data when read_is_pending() returns True.

        Args:
            data (int): A byte value to send.
        """
        # reset flag
        self.clr_reg(self.IC_CLR_TX_ABRT, self.IC_CLR_TX_ABRT__CLR_TX_ABRT)
        status = mem32[self.i2c_base | self.IC_CLR_RD_REQ]
        mem32[self.i2c_base | self.IC_DATA_CMD] = data & 0xFF

    def write_data_is_available(self):
        """Check whether incoming (I2C WRITE) data is available.

        Returns:
            True if data is available, False otherwise.
        """
        # get IC_STATUS
        status = mem32[self.i2c_base | self.IC_STATUS]
        # Check RFNE (Receive FIFO not empty)
        if status & self.IC_STATUS__RFNE:
            # There is data in the Zx FIFO
            return True
        # The Rx FIFO is empty
        return False

    def get_write_data(self, max_size=1):
        """Get incoming (I2C WRITE) data.

        Will return bytes from the Rx FIFO, if present, up to the requested size.

        Args:
            max_size (int): The maximum number of bytes to fetch.
        Returns:
            A list containing 0 to max_size bytes.
        """
        data = []
        while len(data) < max_size and self.write_data_is_available():
            data.append(mem32[self.i2c_base | self.IC_DATA_CMD] & 0xFF)
        return data

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
    print("-------------------------")
    print("Encoder 1 Count: %d      " % (Enc1Count))
    # print("Encoder 2 Count: %d\n" % (Enc2Count))
    print("Encoder 1 Speed: %f      " % (Enc1Speed))
    # print("Encoder 2 Speed: %f" % (Enc2Speed))
    print("-------------------------\n")
    # -----------------
    # Initialize Responder and Controller
    # -----------------
    i2c_responder = I2CResponder(
        RESPONDER_I2C_DEVICE_ID, sda_gpio=GPIO_RESPONDER_SDA, scl_gpio=GPIO_RESPONDER_SCL, responder_address=RESPONDER_ADDRESS
    )
    i2c = I2C(0, scl=GPIO_RESPONDER_SCL, sda=GPIO_RESPONDER_SDA, freq=400000)
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
    bytes_val = int(Enc1Speed).to_bytes(4,'big')
    buffer_out = bytearray([0,bytes_val[0], bytes_val[1], bytes_val[2], bytes_val[3]])
    
    # print("Waiting for data to recieve...")
    # while not i2c_responder.write_data_is_available():
    #     pass
    # data = i2c_responder.get_write_data(max_size=1)
    # for i, value in enumerate(data):
    #     READBUFFER[i] = value
    #     print('Controller: Received I2C READ data: ' + format_hex(READBUFFER))
    i2c.writeto(RESPONDER_ADDRESS, buffer_out)
    
    print("Waiting for write instruction...")
        # We will loop here (polling) until the Controller (running on its own thread) issues an
        # I2C READ.
    if(i2c_responder.read_is_pending()):    
        for value in buffer_out:
            i2c_responder.put_read_data(value)
        # with thread_lock:
            print('   Responder: Transmitted I2C READ data: ' + format_hex(buffer_out))
        
    #time.sleep_ms(100)
    
