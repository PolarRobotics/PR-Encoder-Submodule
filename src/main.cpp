#include "uart.h"
#include "hardware/gpio.h"
#include <Encoder.h>

#define BYTES 4
#define UART_TX_PIN 0
#define UART_RX_PIN 1
#define A_PIN1 2
#define B_PIN1 3
#define A_PIN2 4
#define B_PIN2 5


uint8_t data[BYTES] = {0,0,0,0};
uint8_t recieved[BYTES];
uint8_t encoder_data_a;
uint8_t encoder_data_b;
Encoder runningBack1(A_PIN1, B_PIN1, "");
Encoder runningBack2(A_PIN2, B_PIN2, ""); 
int encoderSpeed;
uint8_t test = 0;
int speed1, speed2;

void readEncoder(uint gpio, uint32_t events);
void readEncoder2(uint gpio, uint32_t events);

void setup() {
  Serial.begin(9600);

  uart_init(uart0, 115200);
  gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
  gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
  runningBack1.initEncoder();
  runningBack2.initEncoder();

  gpio_set_irq_enabled_with_callback(A_PIN1, GPIO_IRQ_EDGE_RISE, true, &readEncoder);
  gpio_set_irq_enabled_with_callback(A_PIN2, GPIO_IRQ_EDGE_RISE, true, &readEncoder2);
}


void loop() {
    speed1 = runningBack1.printSpeed();
    data[0] = speed1 & 0xFF; // Lower 8 bits
    //Serial.println(data[0]);
    data[1] = (speed1 >> 8) & 0xFF; // Upper 8 bits
    
    speed2 = runningBack2.printSpeed();
    data[2] = speed2 & 0xFF;
    data[3] = (speed2 >> 8) & 0xFF;
    
    //Serial.println(runningBack1.encoderACount);
    //Serial.println(data[1]);
    Serial.print("Enc 1: ");
    Serial.print(speed1);
    Serial.print("Enc 2: ");
    Serial.print(speed2);
    Serial.println();
    
    //Serial.println(test);
    uart_write_blocking(uart0, data, BYTES);
  
  
    delay(10);

}

void readEncoder(uint gpio, uint32_t events) {
  runningBack1.countEncoder();
}

void readEncoder2(uint gpio, uint32_t events){
  runningBack2.countEncoder();
}
