void WakeUp()
{
  //Serial.println("interupt fired");
  sleep_disable();    // Disable sleep mode
  detachInterrupt(0); // Removes interupt from assigned pin
  SendMsg("NN", 111);  // 111 - for NANO awake
}
