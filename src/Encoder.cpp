#include <Encoder.h>

// Extern structures 
// std::map<std:string, Encoder*> encoderMap;
Encoder* currentEncoder = nullptr;

/**
 * @brief Constructor for the Encoder class
 * @author Quentin Osterhage
 * Created: 10-18-2023
 * @param int a_channel, int b_channel, String motorName
*/
Encoder::Encoder(int a_channel, int b_channel, String motorName){

    this->a_channel = a_channel;
    this->b_channel = b_channel;
    this->motorName = motorName;
    // // Add the Encoder object to the map with the given a_channel as the key
    // encoderMap[motorName] = this;
}

void readEncoder(){
    if (currentEncoder != nullptr) {
        currentEncoder->countEncoder();
    }
}

void Encoder::initEncoder(){
    pinMode(a_channel, INPUT_PULLUP);
    pinMode(b_channel, INPUT);

    currentEncoder = this;

    attachInterrupt(a_channel, readEncoder, RISING);
}

void Encoder::countEncoder(){

  b_channel_state = digitalRead(b_channel);

  if (b_channel_state == 1) {
    if (encoderACount >= rollerover) {
      encoderACount = 0;
    } else {
      encoderACount = encoderACount + 1;
    }
      
  } else {
    if (encoderACount == 0) {
      encoderACount = rollerover;
    } else {
      encoderACount = encoderACount - 1;
    }
      
  }
}

int Encoder::calcSpeed(int current_count) {
  
  current_time = millis();
  
  //first check if the curret count has rolled over
  if (abs(current_count - prev_current_count) >= rolleroverthreshold) {
    if ((current_count-rolleroverthreshold)>0) {
      omega = float ((current_count-rollerover)-prev_current_count)/(current_time-prev_current_time);
    } else {
      omega = float ((current_count+rollerover)-prev_current_count)/(current_time-prev_current_time);
    }
  } else {
    omega = float (current_count-prev_current_count)/(current_time-prev_current_time);
  }

  prev_current_count = current_count;
  prev_current_time = current_time;

  return omega*156.25f; // 156.25 for 384, 312.5 for 192, 1250 for 48
}

String Encoder::getMotorName(){
  return motorName;
}
