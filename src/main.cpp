#include <Encoder.h>

#define rpmSingle

// Object of HardwareSerial class to allow for uart communication
HardwareSerial uart(2);

// Function Prototype for printData
void printData(encoder_data_packet* data); // prototype for printing data

void setup() {
  // Initialize the serial  communication
  Serial.begin(9600);

  // Initialize the UART communication
  uart.begin(115200, SERIAL_8N1, RX2, TX2);
}

#ifndef rpmSingle
  //#define DEBUG
void loop() {

  int bufferSize = 3; // in bytes

  // Check if there's data available to read
  if (uart.available() >= bufferSize) {
    // Read the data
    uint8_t buffer[bufferSize];
    int test = uart.readBytes(buffer, bufferSize);

    // Combine the two bytes into a single 16-bit integer
    uint16_t value = buffer[0] | (buffer[1] << 8);
    // // Print the combined value
    // Serial.println(value);
  
    // Cast the data to the structure
    encoder_data_packet* data = (encoder_data_packet*)buffer;

    // Print the data attributes
    data->encoder_rpm = value;
    printData(data);
  }
  
  #ifdef DEBUG
  else{
    Serial.print("NO UART\n");
  }
  #endif 
}
#endif


#ifdef rpmSingle
  //#define DEBUG
void loop(){
  int bufferSize = 2;

  // Check if there's data available to read
  if (uart.available() >= bufferSize) {
  // Read the data
  uint8_t buffer[bufferSize];
  int test = uart.readBytes(buffer, bufferSize);

  // Combine the two bytes into a single 16-bit integer
  uint16_t value = buffer[0] | (buffer[1] << 8);

  // Print the integer to serial monitor
  Serial.println(value);
  }

  #ifdef DEBUG
  else{
    Serial.print("NO UART\n");
  }
  #endif
}
#endif

void printData(encoder_data_packet* data){
    Serial.print("encoder_ok: ");
    Serial.print(data->encoder_ok);
    Serial.print("  encoder_rpm: ");
    Serial.print(data->encoder_rpm);
    Serial.print("  encoder_num: ");
    Serial.print(data->encoder_num);
    Serial.print("  encoder_state: ");
    Serial.println(data->encoder_state);
}