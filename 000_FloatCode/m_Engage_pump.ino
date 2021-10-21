/* This sketch engages the Pump for the set time. During this time
    only the VBE sensors and PFmp RPM are read.
    PFmpDirection: 1 = into accumulator / 2 = into bladder
    PFmpVoltage in % of 100, 40% minimum value
    PFmp time in seconds --- millis() function in miliseconds
*/

void EngagePump()
{
  // CHECK IF THE BLADDER IS AT PHYSICAL LIMITS, IF YES EXIT THE FUNCTION
  CalcBladderVol();

  if  (((BF == 1) && (PumpDirection == 1)) || ((BF == 2) && (PumpDirection == 2)))
  {
    return;
  }

  if (PumpDirection == 1)
    PumpDirectionBool = LOW;       // LOW = INTO ACCUMULATOR
  else if (PumpDirection == 2)
    PumpDirectionBool = HIGH;      // HIGH = INTO BLADDER

  digitalWrite(PumpDirectionPin, PumpDirectionBool);
  digitalWrite(ValvePin, HIGH);
  delay(250); // Time for the valve to respond

  // Start pump @100% voltage and then drop to required input
  D2Acmd(100);
  PreviousMillis = millis();       // Reset the pump timer

  //wdt_enable(WDTO_4S);           // enable watchdog timer

  // Verify that the pump started
  delay(500);
  PumpRPM = RPMRead();

  int whilecounter = 1;

  // IF THE READ RPM IS BELLOW 1000 -> THE PUMP DIDN'T START,
  // ALLOW 3 TIMES TO RESTART AND THEN ABORT

  while (PumpRPM < 1000)
  {
    SendMsg("TR", whilecounter); // Pump Failure
    wdt_reset();                   // reset the watchdog each loop

    D2Acmd(0);                     // Send STOP signal to Pump
    delay(1000);

    //    Serial.print(" pump stalled, retry #");
    //    Serial.println(whilecounter);

    PreviousMillis = millis();
    D2Acmd(100);
    delay(500);

    PumpRPM = RPMRead();

    if (whilecounter >= 3)
    {
      SendMsg("PF", 2); // Pump Failure
      digitalWrite(ValvePin, LOW);
      D2Acmd(0);
      delay(500);

      PumpVoltage = 0;
      PumpDirection = 0;
      PumpTime = 0;
      PumpFlag = 2;

      return;
    }

    whilecounter = whilecounter + 1;
  }

  SendMsg("PF", 1); // Send Pump started to RPi
  delay(250);
  D2Acmd(PumpVoltage);

  while (PumpTime * 1000 > (millis() - PreviousMillis - 500))
  {
    wdt_reset();

    PumpRPM = RPMRead();
    SendMsg("RPM", PumpRPM);

    CalcBladderVol();

    if ((BF == 1 && PumpDirection == 1) || (BF == 2 && PumpDirection == 2))
    {
      D2Acmd(0); // Send STOP signal to Pump
      break;
    }
  }

  wdt_reset();

  D2Acmd(0); // Send STOP signal to PFmp
  SendMsg("PF", 0);
  delay(200);
  digitalWrite(ValvePin, LOW);
  
  // Reset the PUMP input variables
  PumpVoltage = 0;
  PumpDirection = 0;
  PumpTime = 0;
  PumpFlag = 0;  
}
