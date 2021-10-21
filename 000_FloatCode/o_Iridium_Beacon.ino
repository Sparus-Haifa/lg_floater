void IridiumBeacon()
{
  unsigned long loopStartTime = millis();

  // Begin listening to the GPS
  //Serial.println(F("Beginning to listen for GPS traffic..."));

  // Look for GPS signal for up to 1 minutes
  //SendMsg("IR", 3);
  //  while (myI2CGPS.available())
  //  {
  //    SendMsg("IR", 4);
  //    tinygps.encode(myI2CGPS.read());
  //    SendMsg("IR", 5);
  //  }

  while ((!tinygps.location.isValid() || !tinygps.date.isValid()) &&
         (millis() - loopStartTime < 1UL * 60UL * 1000UL))
  {
    // original ver - while (myI2CGPS.available())
    if (myI2CGPS.available())
    {
      tinygps.encode(myI2CGPS.read());
    }
  }

  // Did we get a GPS fix?
  if (!tinygps.location.isValid())
  {
    //    Serial.println(F("Could not get GPS fix."));
    //    Serial.print(F("GPS characters seen = "));
    //    Serial.println(tinygps.charsProcessed());
    //    Serial.print(F("Checksum errors = "));
    //    Serial.println(tinygps.failedChecksum());
    SendMsg("GPE", 0);
    return;
  }
  //SendMsg("GPE", 1);

  //Serial.println(F("A GPS fix was found!"));

  // Step 3: Start talking to the RockBLOCK and power it up

  //Serial.println(F("Beginning to talk to the RockBLOCK..."));
  char outBuffer[60]; // Always try to keep message short
  sprintf(outBuffer, "%d%02d%02d%02d%02d%02d,%s%u.%09lu,%s%u.%09lu,%lu,%ld",
          tinygps.date.year(),
          tinygps.date.month(),
          tinygps.date.day(),
          tinygps.time.hour(),
          tinygps.time.minute(),
          tinygps.time.second(),
          tinygps.location.rawLat().negative ? "-" : "",
          tinygps.location.rawLat().deg,
          tinygps.location.rawLat().billionths,
          tinygps.location.rawLng().negative ? "-" : "",
          tinygps.location.rawLng().deg,
          tinygps.location.rawLng().billionths,
          tinygps.speed.value() / 100,
          tinygps.course.value() / 100);

  //  Serial.print(F("Transmitting message '"));
  //  Serial.print(outBuffer);
  //  Serial.println(F("'"));

  int err = modem.sendSBDText(outBuffer);
  if (err != ISBD_SUCCESS)
  {
    //    Serial.print(F("Transmission failed with error code "));
    //    Serial.println(err);
    SendMsg("IRE", err);
    return;
  }
//  else
//  {
//    return;
//  }

  // Sleep
  int elapsedSeconds = (int)((millis() - loopStartTime) / 1000);
  if (elapsedSeconds < BEACON_INTERVAL)
  {
    int delaySeconds = BEACON_INTERVAL - elapsedSeconds;
    //    Serial.print(F("Waiting for "));
    //    Serial.print(delaySeconds);
    //    Serial.println(F(" seconds"));
    delay(1000UL * delaySeconds);
  }

  // Wake
  //Serial.println(F("Wake up!"));

  // EXIT FUNCTION AFTER PRESCRIBED TIME
  if (BeaconT * 1000UL < (millis() - loopStartTime))
    return;
}

//void blinkLED()
//{
//  digitalWrite(ledPin, (millis() / 1000) % 2 == 1 ? HIGH : LOW);
//}
//
//bool ISBDCallback()
//{
//  blinkLED();
//  return true;
//}
//
//#if DIAGNOSTICS
//void ISBDConsoleCallback(IridiumSBD *device, char c)
//{
//  Serial.write(c);
//}
//
//void ISBDDiagsCallback(IridiumSBD *device, char c)
//{
//  Serial.write(c);
//}
//#endif
