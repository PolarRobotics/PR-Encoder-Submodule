#include <Arduino.h>
#include "uart.h"
#include "hardware/gpio.h"
#include <Encoder.h>

#define BYTES 4
#define UART_TX_PIN 0
#define UART_RX_PIN 1
#define A_PIN 2
#define B_PIN 3

uint8_t data[BYTES] = {0,0,0,0};
uint8_t recieved[BYTES];
uint8_t encoder_data_a;
uint8_t encoder_data_b;
Encoder runningBack(A_PIN, B_PIN, "");
int encoderSpeed;


void setup() {
  Serial.begin(9600);

  uart_init(uart0, 115200);
  gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
  gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
  runningBack.initEncoder();
}


void loop() {
  // for(int i = 0; i < BYTES; i++){
  //   data[i] = i;
  // }
    //runningBack.readEncoder(name1, name2);
    for(int i = 0; i < BYTES; i++){
      data[i] = runningBack.printSpeed();
      Serial.println(runningBack.encoderACount);
      delay(10);
    }

    uart_write_blocking(uart0, data, BYTES);
  
  

}
