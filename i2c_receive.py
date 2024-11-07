from machine import mem32

# Standard Library
from machine import Pin, I2C
import time
import _thread

# Local
from i2c_responder import I2CResponder

I2C_FREQUENCY = 100000

RESPONDER_I2C_DEVICE_ID = 0
RESPONDER_ADDRESS = 0x41
GPIO_RESPONDER_SDA = 0
GPIO_RESPONDER_SCL = 1

# Defined Functions for Data Interpretation

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

while True:
    # -----------------
    # Initialize Responder 
    # -----------------
    i2c_responder = I2CResponder(
        RESPONDER_I2C_DEVICE_ID, sda_gpio=GPIO_RESPONDER_SDA, scl_gpio=GPIO_RESPONDER_SCL, responder_address=RESPONDER_ADDRESS
    )

    print('Testing I2CResponder v' + i2c_responder.VERSION)

    print('   Responder: Getting I2C WRITE data...')
    buffer_in = i2c_responder.get_write_data(max_size=11)
    print('   Responder: Received I2C WRITE data: ' + format_hex(buffer_in))
    print()

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

    buffer_out = bytearray([0x09, 0x08])
    for value in buffer_out:
        # We will loop here (polling) until the Controller (running on its own thread) issues an
        # I2C READ.
        while not i2c_responder.read_is_pending():
            pass
        i2c_responder.put_read_data(value)

    time.sleep(1)