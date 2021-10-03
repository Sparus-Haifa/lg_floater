void LightSignal()
{
  switch (LightFlag)
  {
    // Case "1" - Startup successful
    case '1':   digitalWrite(MainRelayPin, HIGH); // enable main relay
      digitalWrite(LightPin, HIGH); // enable main relay
      delay(3000);
      digitalWrite(LightPin, LOW); // enable main relay
      delay(500);
      digitalWrite(LightPin, HIGH); // enable main relay
      delay(3000);
      digitalWrite(LightPin, LOW); // enable main relay
      break;

    // Case "2" - Startup unsuccessful
    case '2':   digitalWrite(MainRelayPin, HIGH); // enable main relay
      digitalWrite(LightPin, HIGH); // enable main relay
      delay(500);
      digitalWrite(LightPin, LOW); // enable main relay
      delay(500);
      digitalWrite(LightPin, HIGH); // enable main relay
      delay(500);
      digitalWrite(LightPin, LOW); // enable main relay
      break;
  }
}
