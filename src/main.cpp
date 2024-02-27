#include <Arduino.h>
#include "uart.h"
#include <Encoder.h>

#define BYTES 255
#define UART_TX_PIN 0
#define UART_RX_PIN 1
#define A_PIN 4
#define B_PIN 5

uint8_t data[BYTES];
uint8_t recieved[BYTES];

void setup() {
  Serial.begin(9600);

  uart_init(uart0, 115200);
  gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
  gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
  
}


void loop() {
  for(int i = 0; i < BYTES; i++){
    data[i] = i;
  }


  while(1){
    uart_write_blocking(uart0, data, BYTES);
    //uart_read_blocking(uart0, recieved, BYTES);

  }
  

}
