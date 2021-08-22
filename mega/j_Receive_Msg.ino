/* This sketch checks the incoming serial buffer for preagreed messages and allocates
   them to the apropriate sketch variables.These are PUMP: voltage/Direction/Time
   Iridium beacon and Signal light flags.
*/

void ReceiveMsg()
{
  while (Serial.available() > 0)
  {
    IncomingIdentifier = Serial.read();
    switch (IncomingIdentifier)
    {
      // Case "V" - pump voltage
      case 'V': PumpVoltage = Serial.parseFloat();
        Serial.print("User message received: ");
        Serial.print(IncomingIdentifier);
        Serial.print(" | Value: ");
        Serial.println(PumpVoltage);
        break;

      // Case "D" - pump direction
      case 'D': PumpDirection = Serial.parseInt();
        Serial.print("User message received: ");
        Serial.print(IncomingIdentifier);
        Serial.print(" | Value: ");
        Serial.println(PumpDirection);
        break;

      // Case "T" - pump ON time
      case 'T': PumpTime = Serial.parseFloat();
        Serial.print("User message received: ");
        Serial.print(IncomingIdentifier);
        Serial.print(" | Value: ");
        Serial.println(PumpTime);
        break;

      // Case "I" - Iridium ON
      case 'I': IridiumFlag = Serial.parseInt();
        Serial.print("User message received: ");
        Serial.print(IncomingIdentifier);
        Serial.print(" | Value: ");
        Serial.println(IridiumFlag);
        break;

      // Case "L" - Light command
      case 'L': LightFlag = Serial.parseInt();
        Serial.print("User message received: ");
        Serial.print(IncomingIdentifier);
        Serial.print(" | Value: ");
        Serial.println(LightFlag);
        break;

      // Case "S" - Surface command
      case 'S': FullSurfaceFlag = Serial.parseInt();
        Serial.print("User message received: ");
        Serial.print(IncomingIdentifier);
        Serial.print(" | Value: ");
        Serial.println(FullSurfaceFlag);
        break;
    }
  }
}
