/* The function performs a full surfacing by actuation the pump with a
    bladder setpoint of 650cc.
    The WHILE loop constantly checks the ACCUMULATOR readings to meassure
    bladder inflation.
*/

void FullSurface(int Direction)
{
  int BladderVolSetPoint;

  // CHECK IF THE BLADDER IS AT PHYSICAL LIMITS, IF YES EXIT THE FUNCTION
  CalcBladderVol();

  if ((BF != 1) && (Direction == 1))
  {
    SendMsg("FS", Direction);
    BladderVolSetPoint = BladderLowerLimit;
    PumpDirectionBool = LOW;
  }

  else if ((BF != 2) && (Direction == 2))
  {
    SendMsg("FS", Direction);
    BladderVolSetPoint = BladderUpperLimit;
    PumpDirectionBool = HIGH;
  }

  else
  {
    return;
  }

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
  SendMsg("RPM", PumpRPM);

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
    SendMsg("RPM", PumpRPM);
    if (whilecounter >= 3)
    {
      SendMsg("PF", 2);
      digitalWrite(ValvePin, LOW);
      return;
    }

    whilecounter = whilecounter + 1;
  }

  

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= WHILE LOOP
  while (BF == 0 || ((BF == 1) && (Direction == 2)) || ((BF == 2) && (Direction == 1)) )
  {
    wdt_reset(); // reset the watchdog each loop
    delay(50);
    SendMsg("RPM", PumpRPM);

    // Calculate bladder volume
    CalcBladderVol();

    if ( ((BF == 1) && (Direction == 1)) || ((BF == 2) && (Direction == 2)))
    {
      D2Acmd(0); // Send STOP signal to pump
      SendMsg("RPM", 0);
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
