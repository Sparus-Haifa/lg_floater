//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= SETUP

void setup()
{
  Serial.begin(115200);
  analogWrite(MotorPin, 0);
  pinMode(DirectionPin, OUTPUT);
  pinMode(MotorPin, OUTPUT);
  analogWrite(MotorPin, 0);

  pinMode(WakeUpPin, INPUT_PULLUP);
  pinMode(LED_BUILTIN, OUTPUT);

  //microswitch
  pinMode(ComPin, INPUT); // common pin
  pinMode(NCPin, OUTPUT); //
  pinMode(NOPin, OUTPUT); //
  
  PreviousMillisOut = millis();

  pinMode(LED_BUILTIN, OUTPUT);
  
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= END of SETUP
}
