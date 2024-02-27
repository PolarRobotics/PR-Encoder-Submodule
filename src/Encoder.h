#include <Arduino.h>
// #include <map>
#include <driver/uart.h>

// PIN DEFINITIONS
// Referenced from: https://docs.google.com/spreadsheets/d/17pdff4T_3GTAkoctwm2IMg07Znoo-iJkyDGN5CqXq3w/edit#gid=0
#define ENC1_NAME "Left Motor"
#define ENC1_CHA 34
#define ENC1_CHB 35
#define ENC2_NAME "Right Motor"
#define ENC2_CHA 36 // VP's GPIO #
#define ENC2_CHB 39 // VN's GPIO #

#define UART_TXD 17 // UART
#define UART_RXD 16 // UART

// Define the UART port and buffer size
const uart_port_t uart_num = UART_NUM_2;
#define BUF_SIZE (1024)

class Encoder{
private:
    String motorName;
    int a_channel;
    int b_channel;
    int encoderACount = 0;
    int rollerover = 2048;
    int b_channel_state = 0;
    int prev_current_count = 0;
    int rolleroverthreshold = 500; //this is based on the fastest speed we expect, if the differace is going to be grater a rollover has likely accured
    unsigned long current_time = 0;
    unsigned long prev_current_time = 0; 
    float omega = 0;

public:
    Encoder(int a_channel, int b_channel, String motorName);
    void initEncoder();
    void countEncoder();
    void printSpeed();
    String getMotorName();
    int calcSpeed(int current_count);
};

// extern std::map<std:string, Encoder*> encoderMap;
extern Encoder* currentEncoder;

// ISR for encoder interrupt
void readEncoder();
