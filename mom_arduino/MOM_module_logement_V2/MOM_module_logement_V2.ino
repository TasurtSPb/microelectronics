#include <ArduinoJson.h>
DynamicJsonDocument doc(1024);

#define PULSE_WIDTH_USEC 10
#define MAX_SENSORS 40


// пины для подключения регистра
int ploadPin = 8; //защелка
int dataPin = 11; //состояние кнопки (бит)
int clockPin = 12; //такт
boolean state_buttons[MAX_SENSORS]; //массив для записи состояния кнопок
boolean flag_print = false; //флаг для вывода при изменении
byte addr_arduino = 4;
byte flag = 0;
byte t = 0;

void setup()
{
  doc["P"]["placement"] = addr_arduino;
  doc["T"]["type"] = "input";
  // для вывода данных в монитор порта и для передачи на Распберри
  Serial.begin(9600);

  // установка режима работа пинов
  pinMode(ploadPin, OUTPUT);
  pinMode(clockPin, OUTPUT);
  pinMode(dataPin, INPUT);
  digitalWrite(clockPin, LOW);
  digitalWrite(ploadPin, HIGH);

  // выводим результат
  //display_pin_values();

  serializeJson(doc["T"], Serial);
  Serial.println();


}

// функция для считывания пинов
void read_shift_regs()
{
  // опрашиваем регистр о состоянии пинов
  digitalWrite(ploadPin, LOW);
  delayMicroseconds(PULSE_WIDTH_USEC);
  digitalWrite(ploadPin, HIGH);

  // считываем полученные данные о пинах
  for (int i = 0; i < MAX_SENSORS; i++)
  {
    if (state_buttons[i] != digitalRead(dataPin)) flag_print = true;
    state_buttons[i] = digitalRead(dataPin);
    digitalWrite(clockPin, HIGH);
    delayMicroseconds(PULSE_WIDTH_USEC);
    digitalWrite(clockPin, LOW);
  }
}

// функция для вывода состояния пинов
  void display_pin_values()
  {
    // перебор всех пинов
    for(int i = 1; i < MAX_SENSORS+1; i++)
    {    
        Serial.print(i);
        Serial.print(" ");
    }
    Serial.println();
  }
  //*/

//*
 void display_pin_state()
  {
  for(int i = 0; i < MAX_SENSORS; i++)
    {

        Serial.print(state_buttons[i]);
        Serial.print(" ");

    }
    Serial.println();


  }
  //*/

/*
 void sendMassage()
  {

  if (flag == 0) Wire.write(byte(SLAVE_ADDRESS));
  else if (flag == 1)
  {
    if (t < MAX_SENSORS)
    {
      Wire.write(byte(dataButton[t]));
      t++;
    }
    else
    {
      t = 0;
      flag = 0;

    }
  }

  }
  */
void loop()
{
  read_shift_regs();
  
   while (Serial.available() != 0)
  {
    if (Serial.peek() == 'S')
    {
      Serial.read();
      //Serial.print(addr_arduino); 
      for (int i = 0; i < MAX_SENSORS; i++)
      {

        //Serial.print(state_buttons[i]);
        doc["P"]["data"][i]["key"]=i+1;
        doc["P"]["data"][i]["status"]=state_buttons[i];
      }
      serializeJson(doc["P"], Serial);
      Serial.println();
    }
    else if (Serial.peek() == 'T')
    {
      Serial.read();
      serializeJson(doc["T"], Serial);
 
      Serial.println();
    }
    else Serial.read();
  }
  
} 
