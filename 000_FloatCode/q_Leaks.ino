void Leaks()
{
  //-=-=-=-=-=-=-=-=-=-=-=-=-= VBE
  int j = 2;
  int VBELeakVal[j];

  digitalWrite(VBEoutPin, HIGH);
  delay(20);

  for (int i = 0; i <= j; i++)
  {
    VBELeakVal[i] = analogRead(VBEinPin);
    //    delay(10);
    //    Serial.print("Sensor reading ");
    //    Serial.print(i);
    //    Serial.print(": " );
    //    Serial.println(VBELeakVal[i]);
    delay(20);
  }

  digitalWrite(VBEoutPin, LOW);
  int  AvrgSensorVal = 0;
  for (int i = 0; i <= j; i++)
  {
    AvrgSensorVal = AvrgSensorVal + VBELeakVal[i];
  }

  if ( AvrgSensorVal / (j + 1) > LeakTH )
    VBEleakFlag = 1;
  else VBEleakFlag = 0;

  //  Serial.print("VBE leak value (in %):");
  //  Serial.print(AvrgSensorVal);
  //  Serial.print(", VBE leak flag:");
  //  Serial.println(VBEleakFlag);
  //  Serial.println("");
  //  delay(500);

  // HullLeakFlag = digitalRead(leakPin);   // Read the Leak Sensor Pin

  //-=-=-=-=-=-=-=-=-=-=-=-=-= HULL

  HullLeakFlag = digitalRead(HullLeakPin);   // Read the Leak Sensor Pin
}
