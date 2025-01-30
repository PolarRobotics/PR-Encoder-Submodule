"""I2CResponder Test Application.

NOTE: This module uses I2C Controller/Responder nomenclature per
      https://www.eetimes.com/its-time-for-ieee-to-retire-master-slave/

This test application runs on a single Raspberry Pico to exercise the API of the
I2CResponder() class.

To execute this test application you will need to wire I2C0 and I2C1 together as follows:


   +---- 3.3V -------------------------------------------------------------------+
   |                                                                             |
   |                      +======================= Pico ====================+    |
   |   1K Ohm             I                                                 I    |
   +--/\/\/\/----O--------I Pin 1 (GP0, I2C0 SDA)                    PIN 40 I    |
   |             |        I                                                 I    |
   |             |    +---I Pin 2 (GP1, I2C0 SCL)                    PIN 39 I    |
   |             |    |   I                                                 I    |
   |             |    |   I Pin 2                                    PIN 38 I    |
   |             |    |   I                                                 I    |
   |             |--------I Pin 4 (GP2, I2C1 SDA)                    PIN 37 I    |
   |   1K Ohm         |   I                                                 I    |
   +--/\/\/\/---------O---I Pin 5 (GP3, I2C1 SCL)         (3V3(OUT)) PIN 36 I----+
                          I                                                 I
                          I                                                 I
"""

# Standard Library
from machine import Pin, I2C, 
import time
import _thread

from machine import mem32

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

CONTROLLER_I2C_DEVICE_ID = 1
GPIO_CONTROLLER_SDA = 2
GPIO_CONTROLLER_SCL = 3

RESPONDER_I2C_DEVICE_ID = 0
RESPONDER_ADDRESS = 0x41
GPIO_RESPONDER_SDA = 0
GPIO_RESPONDER_SCL = 1

READBUFFER = [0, 0]

def main():

    # -----------------
    # Initialize Responder and Controller
    # -----------------
    i2c_responder = I2CResponder(
        RESPONDER_I2C_DEVICE_ID, sda_gpio=GPIO_RESPONDER_SDA, scl_gpio=GPIO_RESPONDER_SCL, responder_address=RESPONDER_ADDRESS
    )
    i2c_controller = I2C(
        CONTROLLER_I2C_DEVICE_ID,
        scl=Pin(GPIO_CONTROLLER_SCL),
        sda=Pin(GPIO_CONTROLLER_SDA),
        freq=I2C_FREQUENCY,
    )
    print('Testing I2CResponder v' + i2c_responder.VERSION)


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
    buffer_out = bytearray([-30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    while True:
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
        

# def thread_i2c_controller_read(i2c_controller, thread_lock):
#     """Issue an I2C READ on the Controller."""
#     with thread_lock:
#         print('Controller: Initiating I2C READ...')
#     # NOTE: This operation will BLOCK until the Responder supplies the requested
#     #       data, which is why we are running it on a second thread (on the second
#     #       Pico core).
#     data = i2c_controller.readfrom(RESPONDER_ADDRESS, 2)

#     for i, value in enumerate(data):
#         READBUFFER[i] = value


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


if __name__ == "__main__":
    main()