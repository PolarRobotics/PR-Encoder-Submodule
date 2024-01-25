#include <Encoder.h>
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

    // Initialize the SPI interface
    _spi_init(SPI_INSTANCE, SPI_BAUD_RATE);

    // Set the SPI pins
    gpio_set_function(SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MISO_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_CS_PIN, GPIO_FUNC_SPI);
}

void loop() {
    uint8_t buffer[64];
    // Read data from the SPI interface
    uint8_t data = spi_read_blocking(SPI_INSTANCE, NULL, buffer, 64);

    // Print the received data
    printf("Received: %d\n", data);
}


void printData(encoder_data_packet* data){
    Serial.print("encoder_rpmOne: ");
    Serial.println(data->encoder_rpmOne);
    Serial.println("encoder_rpmTwo: " + data->encoder_rpmTwo);
}