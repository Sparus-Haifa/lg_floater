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
        SendMsg("V", PumpVoltage);
        break;

      // Case "D" - pump direction
      case 'D': PumpDirection = Serial.parseInt();
        SendMsg("D", PumpDirection);
        break;

      // Case "T" - pump ON time
      case 'T': PumpTime = Serial.parseFloat();
        SendMsg("T", PumpTime);
        break;

      // Case "I" - Iridium ON
      case 'I': IridiumFlag = Serial.parseInt();
        SendMsg("I", IridiumFlag);
        break;

      // Case "L" - Light command
      case 'L': LightFlag = Serial.parseInt();
        SendMsg("L", LightFlag);
        break;

      // Case "S" - Surface command
      case 'S': FullSurfaceFlag = Serial.parseInt();
        SendMsg("S", FullSurfaceFlag);
        break;
    }
  }
}
