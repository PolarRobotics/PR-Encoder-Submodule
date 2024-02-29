#include <Encoder.h>
#include "hardware/gpio.h"



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

 void readEncoder(uint gpio, uint32_t events) {
    Serial.println("Interrupt triggered");
    //if (currentEncoder != nullptr) {
        currentEncoder->countEncoder();
    //}
}

void Encoder::initEncoder(){
    _gpio_init(this->a_channel);
    _gpio_init(this->b_channel);
    gpio_set_dir(this->a_channel, GPIO_IN);
    gpio_set_dir(this->b_channel, GPIO_IN);
    gpio_pull_up(this->a_channel);

    currentEncoder = this;

    //attachInterrupt(a_channel, readEncoder, RISING);
    gpio_set_irq_enabled_with_callback(this->a_channel, GPIO_IRQ_EDGE_RISE, true, readEncoder);
}

void Encoder::countEncoder(){

  b_channel_state = gpio_get(this->b_channel);

  if (b_channel_state == 1) {
    if (encoderACount >= rollerover) {
      encoderACount = 0;
      Serial.println("encoderACount = 0");
      delay(100);
    } else {
      encoderACount = encoderACount + 1;
      Serial.println("encoderACount incremented");
      delay(100);
    }
      
  } else {
    if (encoderACount == 0) {
      encoderACount = rollerover;
      Serial.println("encoderACount = rollerover");
      delay(100);
    } else {
      encoderACount = encoderACount - 1;
      Serial.println("encoderACount decremented");
      delay(100);
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

int Encoder::printSpeed(){
  return this->calcSpeed(this->encoderACount);

}
