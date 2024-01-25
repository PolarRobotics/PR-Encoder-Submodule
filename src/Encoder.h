// #include <map>
#include <Arduino.h>
#include <spi.h>

// PIN DEFINITIONS
// Referenced from: https://docs.google.com/spreadsheets/d/17pdff4T_3GTAkoctwm2IMg07Znoo-iJkyDGN5CqXq3w/edit#gid=0
#define ENC1_NAME "Left Motor"
#define ENC1_CHA 34
#define ENC1_CHB 35
#define ENC2_NAME "Right Motor"
#define ENC2_CHA 36 // VP's GPIO #
#define ENC2_CHB 39 // VN's GPIO #

/**
 * UART Stuff
**/

#define TX2 17 // UART
#define RX2 12 // UART

// Define the UART port and buffer size
#define BUF_SIZE (1024)

//Define the data packet structure
struct encoder_data_packet {
  int16_t encoder_rpmOne : 16;
  int16_t encoder_rpmTwo : 16;
}__attribute__((packed));

/**
 * Encoder Class
 * 
**/

class Encoder{
private:
    String motorName; // name of the Motor monitored by this Encoder 
    int a_channel; // A channel pin for this Encoder 
    int b_channel; // B channel pin for this Encoder 
    int rollerover = 2048; // Resolution of the encoder
    int b_channel_state = 0; // Used to determine the irection in which the motor is turning
    int rolleroverthreshold = 500; //this is based on the fastest speed we expect, if the differace is going to be grater a rollover has likely accured
    
    // Variables used to calculate the speed of the motor in RPM
    int current_count = 0; 
    int prev_current_count = 0;
    unsigned long current_time = 0;
    unsigned long prev_current_time = 0; 
    float omega = 0;
    
public:
    Encoder(int a_channel, int b_channel, String motorName);
    void initEncoder();
    void printSpeed();
    String getMotorName();
    int calcSpeed();
    void countEncoder();
};


/**
 * Handling the ISR
**/


// A pointer to an instance of the Encoder class, initalized to "this" when Encoder is initalized (initEncoder)
extern Encoder* currentEncoder;


void readEncoder();


// Could potentially create a map of function pointers with each function bound to a specific encoder instance
// extern std::map<std:string, Encoder*> encoderMap;

// IN SETUP LOOP
    // isrMap[channel_a1] = std::bind(&Encoder::countEncoder, &encoder1);
    // isrMap[channel_a2] = std::bind(&Encoder::countEncoder, &encoder2);

    // attachInterrupt(digitalPinToInterrupt(channel_a1), isrMap[channel_a1], RISING);
    // attachInterrupt(digitalPinToInterrupt(channel_a2), isrMap[channel_a2], RISING);