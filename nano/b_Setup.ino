
//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= SETUP

void setup()
{
  Serial.begin(115200);
//  Serial1.begin(115200);
//  Serial2.begin(115200);

  pinMode(MotorPin, OUTPUT);
  pinMode(DirectionPin, OUTPUT);
  analogWrite(MotorPin, 0);
  pinMode(interruptPin, INPUT_PULLUP);
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= END of SETUP
}
