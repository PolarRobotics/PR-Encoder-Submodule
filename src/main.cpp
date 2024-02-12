#include <Encoder.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"

// Define SPI instance, SCK pin, MISO pin, and optional CS pin
#define SPI_INSTANCE spi0
#define SCK_PIN  2
#define MISO_PIN  4
#define CS_PIN  5

void setup() {
    stdio_init_all();

    // Configure SPI as a slave device
    spi_init(SPI_INSTANCE,  1000 *  1000); //  1 MHz clock speed
    gpio_set_function(SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(MISO_PIN, GPIO_FUNC_SPI);
    if (CS_PIN != PICO_DEFAULT_SPI_CSN_PIN) {
        gpio_set_function(CS_PIN, GPIO_FUNC_SPI);
    }
    spi_set_format(SPI_INSTANCE,  16, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
}

uint16_t read_spi_data() {
    uint16_t data =  0;
    spi_read_blocking(SPI_INSTANCE, NULL, &data,  2); // Read  2 bytes (16 bits)
    return data;
}

void loop() {
    uint16_t received_data = read_spi_data();
    printf("Received data: %u\n", received_data);
    sleep_ms(1000); // Wait for a second before reading again
}

int main() {
    setup();
    while (true) {
        loop();
    }
}