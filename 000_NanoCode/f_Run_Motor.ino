void RunMotor()
{
  digitalWrite(DirectionPin, HIGH);
  analogWrite(MotorPin, 255);
  delay(MotorTimeHigh);
  analogWrite(MotorPin, 0);
  delay(2000);





  digitalWrite(DirectionPin, LOW);
  analogWrite(MotorPin, 255);
  // delay(MotorTimeLow);
  digitalWrite(NCPin, HIGH);
  digitalWrite(NOPin, LOW);

  MS = digitalRead(ComPin);
  //wait microswitch
  while (MS == HIGH)
  {
    delay(50);
    MS = digitalRead(ComPin);
    // Serial.println(MS);
  }


  //stop motor
  analogWrite(MotorPin, 0);
  digitalWrite(NCPin, LOW);
  digitalWrite(NOPin, LOW);
//  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
//  delay(2500);                       // wait for a second
//  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
//  delay(1000);  
//  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
//  delay(2500);                       // wait for a second
//  digitalWrite(LED_BUILTIN, LOW); 
}
