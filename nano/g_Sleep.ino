void Sleep()
{
  sleep_enable();                       // Enable sleep mode
  attachInterrupt(1, WakeUp, HIGH);     // attachInterrupt(interrupt pin (0 = d2, 1 = d3), Interupt func(), Pin position );
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);  // Set desired sleep mode
  SendMsg("NN", 222);                   // 222 - for NANO ASLEEP
  sleep_cpu();                          // Activate sleep mode
}
