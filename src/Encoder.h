#include <Arduino.h>
// #include <map>


// PIN DEFINITIONS
// Referenced from: https://docs.google.com/spreadsheets/d/17pdff4T_3GTAkoctwm2IMg07Znoo-iJkyDGN5CqXq3w/edit#gid=0
#define ENC1_NAME "Left Motor"
#define ENC1_CHA 34
#define ENC1_CHB 35
#define ENC2_NAME "Right Motor"
#define ENC2_CHA 36 // VP's GPIO #
#define ENC2_CHB 39 // VN's GPIO #

class Encoder{
private:
    String motorName;
    int a_channel;
    int b_channel;
    int rollerover = 10000;
    int b_channel_state = 0;
    int prev_current_count = 0;
    int rolleroverthreshold = 2000; //this is based on the fastest speed we expect, if the differace is going to be grater a rollover has likely accured
    unsigned long current_time = 0;
    unsigned long prev_current_time = 0; 
    float omega = 0;

public:
    Encoder(int a_channel, int b_channel, String motorName);
    void initEncoder();
    void countEncoder();
    int printSpeed();
    int encoderACount = 0;
    String getMotorName();
    int calcSpeed(int current_count);
    //void readEncoder(uint gpio, uint32_t events);
};

// extern std::map<std:string, Encoder*> encoderMap;
extern Encoder* currentEncoder;

// ISR for encoder interrupt
void readEncoder(uint gpio, uint32_t events);
