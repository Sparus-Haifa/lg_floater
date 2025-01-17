void loop()
{
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= RESET WATCHDOG TIMER
  wdt_reset(); // reset the watchdog each loop
  PreviousMillis = millis();

  SendMsg("LC", LoopCounter);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= STOP PUMP
  // If the pump is active but the remaining pumping time is shorter than 1 sec
  // the sketch will hold here and will stop the pump when the clock runs out.

  //  if (PumpFlag = 1 && millis() - PreviousMillis > (PumpTime - 1) * 1000)
  //    PumpStop();

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= CHECK LEAKS
  // Check both leak detectors and initiate emergency surfacing in case a
  // leak is detected. Raise the relevant leak flag and send to RPi.
  // This is an infinite loop which will keep transmiting the float's
  // location after emergency surfacing is completed.

  Leaks();
  SendMsg("HL", HullLeakFlag);
  SendMsg("EL", VBEleakFlag);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= EMERGENCY LEAK SIMULATION
  //  if (millis() >= 1000UL * 60UL * LeakNow)
  //  {
  //    // HullLeakFlag = 1;
  //    VBEleakFlag = 1;
  //  }

  if ((HullLeakFlag == 1) || (VBEleakFlag == 1))
  {
    while (1)
    {
      SendMsg("FS", 2);
      FullSurface(2);
      wdt_disable();
      IridiumBeacon();
      wdt_enable(WDTO_4S);
    }
  }

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= RECEIVE INCOMING DATA
  // Check the incoming serial buffer

  ReceiveMsg();

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= END MISSION
  // If the surface/end-mission command is received the bladder is fully inflated.
  // 1 - Submerge  |  2 - Surface

  if ((FullSurfaceFlag == 1) || (FullSurfaceFlag == 2))
  {
          SendMsg("FS", FullSurfaceFlag);
FullSurface(FullSurfaceFlag);
    FullSurfaceFlag = 0;
    SendMsg("FS", FullSurfaceFlag);
  }

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= IRIDIUM BEACON
  // The Beacon is engaged when the RPi identifies sea surface via pressure difference
  // on the pressure sensors

  if (IridiumFlag == 1)
  {
    wdt_disable();
    SendMsg("IR", 1);
    IridiumBeacon();
    IridiumFlag = 0;
    SendMsg("IR", 0);
  }

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= PUMP ACTUATION
  // If all three pump actuation parameters are non-zero then start pump

  if ((PumpVoltage != 0) && ((PumpDirection == 1) || (PumpDirection == 2)) && (PumpTime != 0))
  {
    //SendMsg("V", 1);
    //    SendMsg("V", PumpVoltage);
    //    SendMsg("D", PumpDirection);
    //    SendMsg("T", PumpTime);
    EngagePump();
  }

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= BOTTOM MUX SENSORS
  // Read bottom sensors
  myMux.begin(BottomMux);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= BOTTOM TEMP
  wdt_reset();
  ReadTemp(0);
  SensorsBottom[0] = TempSensor.temperature();
  SendMsg("BT1", SensorsBottom[0]);

  ReadTemp(1);
  SensorsBottom[1] = TempSensor.temperature();
  SendMsg("BT2", SensorsBottom[1]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= BOTTOM PRESS

  ReadPress(2);
  SensorsBottom[2] = PresSensor.pressure();
  SendMsg("BP1", SensorsBottom[2]);

  ReadPress(3);
  SensorsBottom[3] = PresSensor.pressure();
  SendMsg("BP2", SensorsBottom[3]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= HYDRAULIC PRESS
  ReadPress(4);
  SensorsBottom[4] = PresSensor.pressure();
  SendMsg("HP", SensorsBottom[4]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= TOP MUX SENSORS
  myMux.begin(TopMux);
  wdt_reset();

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= TOP TEMP
  ReadTemp(2);
  SensorsTop[2] = TempSensor.temperature();
  SendMsg("TT1", SensorsTop[2]);

  ReadTemp(4);
  SensorsTop[4] = TempSensor.temperature();
  SendMsg("TT2", SensorsTop[4]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= TOP PRESS
  ReadPress(3);
  SensorsTop[3] = PresSensor.pressure();
  SendMsg("TP1", SensorsTop[3]);

  ReadPress(5);
  SensorsTop[5] = PresSensor.pressure();
  SendMsg("TP2", SensorsTop[5]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= BLADDER VOLUME
  CalcBladderVol();

  //-=-=-=-=-=-=-=-=-=-=-=-=-= BNO080 IMU

  if (myIMU.dataAvailable() == true)
  {
    LinearAccelerometer();
    SendMsg("X", X_acc);
    SendMsg("Y", Y_acc);
    SendMsg("Z", Z_acc);
  }

  //-=-=-=-=-=-=-=-=-=-=-=-=-= BR Ping
  AltPing();
  SendMsg("PD", PingDistance);
  SendMsg("PC", PingConfidence);

  //-=-=-=-=-=-=-=-=-=-=-=-=-= END OF VOID LOOP
  LoopCounter = LoopCounter + 1;
  //  Serial.print("Loop time: ");
  //  Serial.print((millis() - PreviousMillis));
  //  Serial.println("sec");
  //  Serial.println(" ");
}
