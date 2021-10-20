/* The function performs a full surfacing by actuation the pump with a
    bladder setpoint of 650cc.
    The WHILE loop constantly checks the ACCUMULATOR readings to meassure
    bladder inflation.
*/

void FullSurface()
{
  SendMsg("YK", 1);
  // CHECK IF THE BLADDER IS AT PHYSICAL LIMITS, IF YES EXIT THE FUNCTION
  CalcBladderVol();
  SendMsg("BV", BladdVol);

  if (BF == 2)
  {
    SendMsg("YK", 2);
    return;
  }

SendMsg("YK", 3);
  int BladderVolSetPoint = BladderUpperLimit, PumpDirectionBool = HIGH;

  // Reset timers
  PreviousMillis = millis();
  //wdt_enable(WDTO_2S); // enable watchdog timer

  // Feed commands into pump
  digitalWrite(PumpDirectionPin, PumpDirectionBool);
  digitalWrite(ValvePin, HIGH);
  delay(200);
  D2Acmd(100);

  // Verify that the Pump started
  delay(500);
  PumpRPM = RPMRead();

  int whilecounter = 1;

  // IF THE READ RPM IS BELLOW 1000 -> THE PUMP DIDN'T START,
  // ALLOW 3 TIMES TO RESTART AND THEN ABORT
  while (PumpRPM < 1000)
  {
    wdt_reset(); // reset the watchdog each loop

    D2Acmd(0); // Send STOP signal to pump
    delay(1000);

    PreviousMillis = millis();
    D2Acmd(100);
    delay(1000);

    PumpRPM = RPMRead();
    if (whilecounter >= 3)
    {
      SendMsg("PF", 2);
      digitalWrite(ValvePin, LOW);
      return;
    }

    whilecounter = whilecounter + 1;
  }

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= WHILE LOOP
  while (BF == 0)
  {
    wdt_reset(); // reset the watchdog each loop
    delay(50);

    // Calculate bladder volume
    CalcBladderVol();

    if (BF != 0)
    {
      D2Acmd(0); // Send STOP signal to pump
      break;
    }
    //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= END of WHILE LOOP
  }

  wdt_reset();
  //wdt_disable(); // disable watchdog after exit from while() loop

  D2Acmd(0); // Send STOP signal to pump
  delay(200);
  digitalWrite(ValvePin, LOW);
}
