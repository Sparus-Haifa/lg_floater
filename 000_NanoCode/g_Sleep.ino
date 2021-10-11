void Sleep()
{
  attachInterrupt(1, WakeUp, LOW);  // attachInterrupt(interrupt pin (0 = d2, 1 = d3), Interupt func(), Pin position );
//  delay(500);
  
  SendMsg("NN", 222);               // 222 - for NANO ASLEEP
//
//  delay(500);
//
//  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
//  delay(1000);                       // wait for a second
//  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
//  delay(500);
//  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
//  delay(1000);                       // wait for a second
//  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
//  delay(500);
//
//  SendMsg("NN", 18);
  // delay(1000);
  
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
  
//  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
//  delay(500);                       // wait for a second
//  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
//  delay(200);
//  SendMsg("NN", 12);    // 111 - for NANO awake
//  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
//  delay(500);                       // wait for a second
//  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
//  delay(200);
//  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
//  delay(500);                       // wait for a second
//  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
//  SendMsg("NN", 13);    // 111 - for NANO awake
  
  detachInterrupt(1);    // Removes interupt from assigned pin
  SendMsg("NN", 111);    // 111 - for NANO awake
  PreviousMillisOut = millis();
  PreviousMillisIn = millis();
  LoopFlag = 0;
}
