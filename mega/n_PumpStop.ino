/* This function was meant to allow to run the main loop while the pump is active. 
 * Currently unused 
 */
 
void PumpStop()
{
  while (millis() - PreviousMillis <= PumpTime * 1000)
  {
    delay(50);
  }
  analogWrite(PumpControlPin, 0); // Send STOP signal to pump
  delay(200);
  digitalWrite(ValvePin, LOW);
  PumpTime = 0;
  PumpFlag = 0;
}
