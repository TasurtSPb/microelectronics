#include "SoftwareSerial.h"
#include  "Servo.h"
#include <ArduinoJson.h>

DynamicJsonDocument doc(1024);

#define door_sensor 2
#define motor_pin 3
#define rfid_rx 9
#define rfid_tx 8
#define green_led_pin 6
#define red_led_pin 7

int motor_speed = 90; //от 0 до 100

int start_angle = 180;
int stop_angle = 120;
int motor_distance = 15; //добавочный угол после срабатывания датчика
int motor_state; //состояние замка 0-открыт, 1-закрыт
int state_count = 0; // состояние программы

boolean leds_state = 0; //состояние светодиода 0-красный, 1-зеленый
boolean first_close = 0;

String addr_arduino = "lock";

String card_numder = "";
byte card_numder_buf[] = {};

SoftwareSerial RFID(rfid_rx, rfid_tx); // RX, TX
Servo motor;

void setup() {
  
  doc["T"]["type"] = addr_arduino;


  Serial.begin(9600);
  RFID.begin(9600);
  motor.attach(motor_pin);

  pinMode(red_led_pin, OUTPUT);
  pinMode(green_led_pin, OUTPUT);

  state_count = 4;

}

void loop() {

  //Serial.println(state_count);
  
  switch (state_count)
  {
    case 1:
      open_RFID_read_send();
      break;
    case 2:
      monitoring_serial_for_open();
      break;
    case 3:
      open_module();
      break;
    case 4:
      close_module();
      break;
    case 5:
      // do something
      break;
    case 6:
      close_RFID_read();
      break;

  }
}

void open_RFID_read_send() //state_count = 1

{
  type_check();
  int a = 0;
  if(RFID.read() == 0x02)
  {
    while (RFID.peek() != 0x03)
    {
      card_numder += (char)RFID.read();
      delay(20);
      //Serial.print(a);
      a++;
    }
    RFID.read();
    doc["C"]["card"] = card_numder;
      //Serial.println();
      serializeJson(doc["C"], Serial);
      Serial.println();
      
      state_count = 2;
      //state_count = 1;
  }
  while (RFID.available() > 0)
  {
    RFID.read();
  }
  card_numder = "";
  type_check();
  delay(100);
}

void monitoring_serial_for_open() //state_count = 2
{
  for(int i=0; i<100; i++)
  {
    if (Serial.available() == 0)
  {
    delay(10);
    state_count = 1;
    
  } 
    else break;
  }
  while (Serial.available() != 0)
  {
    if (Serial.peek() == 'O')
    {
      Serial.read();
      state_count = 3;
      
    }
    else if (Serial.peek() == 'T')
    {
      Serial.read();
      serializeJson(doc["T"], Serial);
      Serial.println();
      
      state_count = 1;
    }
    else 
    {
      Serial.read();
      
    }
  }
  
}

void open_module() //state_count = 3
{
 
  while (RFID.available() > 0)
  {
    RFID.read();
  }
  for (int i = start_angle; i > stop_angle; i--)
    {
      motor.write(i);
      delay(100 - motor_speed);
      if (digitalRead(door_sensor))
      {
        motor.write(i + motor_distance);
        delay(150);
        //Serial.println("Stop onening");
        green();
        state_count = 6;
        break;
      }
    }
  type_check();

}

void close_module() //state_count = 4
{
  //type_check();
  while (RFID.available() > 0)
  {
    RFID.read();
  }
  if (first_close == 0)
  {
    motor.write(start_angle);
    delay(300);
    first_close == 1;
  }
  else 
  {
    for (int i = stop_angle; i < start_angle; i++)
  
  {
    motor.write(i);
    delay(100 - motor_speed);
  }
  }
  if (digitalRead(door_sensor))
  {
    motor.write(stop_angle);
    delay(200);
    for (int i = 0; i < 12; i++)
    {
      red();
      delay(100);
      green();
      delay(100);
    }
    state_count = 6;
  }
  else
  {
    state_count = 1;
    red();
  }
  type_check();
}

void close_RFID_read() //state_count = 6
{
  type_check();
  if (RFID.available() > 0)
  {
    RFID.read();
    if (RFID.available() == 0) state_count = 4;

  }
  type_check();

}

void red()
{
  type_check();
  digitalWrite(red_led_pin, HIGH);
  digitalWrite(green_led_pin, LOW);
}

void green()
{
  type_check();
  digitalWrite(green_led_pin, HIGH);
  digitalWrite(red_led_pin, LOW);
}

void type_check()
{
 while (Serial.available() > 0)
  {
    byte R = Serial.read();
    if (R == 'T')
    {
      serializeJson(doc["T"], Serial);
      Serial.println();
      
    }
  }

}
