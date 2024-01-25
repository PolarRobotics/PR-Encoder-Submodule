#include <Encoder.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"

#define rpmSingle

// Object of HardwareSerial class to allow for uart communication

// Function Prototype for printData
void printData(encoder_data_packet* data); // prototype for printing data


#define SPI_INSTANCE spi0
#define SPI_BAUD_RATE 1000000
#define SPI_SCK_PIN 2
#define SPI_MISO_PIN 4
#define SPI_MOSI_PIN 3
#define SPI_CS_PIN 5

void setup() {
    stdio_init_all();

    // Initialize the SPI interface
    _spi_init(SPI_INSTANCE, SPI_BAUD_RATE);

    // Set the SPI pins
    gpio_set_function(SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MISO_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_CS_PIN, GPIO_FUNC_SPI);
}

void loop() {
    // Read data from the SPI interface
    uint8_t data = spi_read_blocking(SPI_INSTANCE, NULL);

    // Print the received data
    printf("Received: %d\n", data);
}


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