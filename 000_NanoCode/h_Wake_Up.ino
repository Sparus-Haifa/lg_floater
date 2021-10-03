void WakeUp()
{
  detachInterrupt(1);    // Removes interupt from assigned pin
  SendMsg("NN", 111);    // 111 - for NANO awake
//
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
//  
//  PreviousMillisOut = millis();
//  PreviousMillisIn = millis();
}
