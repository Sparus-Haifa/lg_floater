
//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= SETUP

void setup()
{
  Serial.begin(115200);

  pinMode(MotorPin, OUTPUT);
  pinMode(DirectionPin, OUTPUT);
  analogWrite(MotorPin, 0);
  pinMode(interruptPin, INPUT_PULLUP);

  PreviousMillisOut = millis();
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= END of SETUP
}
