#include <Encoder.h>
#include "pico/stdlib.h"

#define rpmSingle

// Object of HardwareSerial class to allow for uart communication

// Function Prototype for printData
void printData(encoder_data_packet* data); // prototype for printing data

void setup(){
  stdio_init_all();


}
void loop(){

}