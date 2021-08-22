/* This sketch engages the pump for the set time. During this time
    only the VBE sensors and Pump RPM are read.
    PumpDirection: 1 = into accumulator / 2 = into bladder
    PumpVoltage in % of 100, 40% minimum value
    Pump time in seconds --- millis() function in miliseconds
*/

void EngagePump()
{
  // CHECK IF THE BLADDER IS AT PHYSICAL LIMITS, IF YES EXIT THE FUNCTION
  CalcBladderVol();

  if ((BladdVol >= BladderUpperLimit) || (BladdVol <= BladderLowerLimit))
  {
    analogWrite(PumpControlPin, 0); // Send STOP signal to pump
    //Serial.println("Bladder volume out of bounds!!!");
    return;
  }

  if (PumpD == 1)
    PumpDirection = LOW;   // LOW = INTO ACCUMULATOR
  else if (PumpD == 2)
    PumpDirection = HIGH;  // HIGH = INTO BLADDER

  digitalWrite(PumpDirectionPin, PumpDirection);
  digitalWrite(ValvePin, HIGH);
  delay(250); // Time for the valve to respond

  PreviousMillis = millis(); // Reset the pump timer

  // Start pump @100% voltage and then drop to required input
  analogWrite(PumpControlPin, 255);

  //wdt_enable(WDTO_4S); // enable watchdog timer

  // Verify that the Pump started
  delay(850);
  PumpRPM = RPMRead();

  int whilecounter = 1;

  // IF THE READ RPM IS BELLOW 1000 -> THE PUMP DIDN'T START, ALLOW 3 TIMES TO RESTART
  // OR ABORT
  while (PumpRPM < 1000)
  {
    wdt_reset(); // reset the watchdog each loop

    analogWrite(PumpControlPin, 0); // Send STOP signal to pump
    delay(1000);

    //    Serial.print(" Pump stalled, retry #");
    //    Serial.println(whilecounter);

    PreviousMillis = millis();
    analogWrite(PumpControlPin, 255);
    //Serial.println(" Pump restarted ");
    delay(1000);

    PumpRPM = RPMRead();
    //    Serial.print("Pump RPM: ");
    //    Serial.println( PumpRPM );

    if (whilecounter >= 3)
    {
      return;
    }

    whilecounter = whilecounter + 1;
  }

  SendMsg("PU", 1); // Send pump started to RPi
  delay(250);
  analogWrite(PumpControlPin, PumpVoltage * 255 / 100);

  while (PumpTime > PreviousMillis)
  {
    wdt_reset();

    PumpRPM = RPMRead();
    while (PumpRPM < 1000)
    {
      // If the pump stalls retry to start the pump until it starts
      PreviousMillis = millis();
      analogWrite(PumpControlPin, 255);
      delay(1000);
      analogWrite(PumpControlPin, PumpVoltage * 255 / 100);
    }

    // Calculate bladder volume
    CalcBladderVol();
    SendMsg("BV", BladdVol);
    
    if ((BladdVol >= BladderUpperLimit) || (BladdVol <= BladderLowerLimit))
    {
      analogWrite(PumpControlPin, 0); // Send STOP signal to pump
      //Serial.println("Bladder volume out of bounds!!!");
      break;
    }
  }

  wdt_reset();

  analogWrite(PumpControlPin, 0); // Send STOP signal to pump
  SendMsg("PU", 0);
  delay(200);
  digitalWrite(ValvePin, LOW);

  // Reset the PUMP input variables
  PumpVoltage = 0;
  PumpDirection = 0;
  PumpTime = 0;
  PumpFlag = 0;
}
