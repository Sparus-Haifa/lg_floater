
void loop()
{
  while (J < 1000)
  {
    if (myICM.dataReady())
    {
      myICM.getAGMT();               // The values are only updated when you call 'getAGMT'
      //printRawAGMT( myICM.agmt );  // Uncomment this to see the raw values, taken directly from the agmt structure
      printScaledAGMT(&myICM);     // This function takes into account the scale settings
      // from when the measurement was made to calculate the values with units

      //SD CARD///////
      myLog.syncFile();
      /////////////
      J = J + 1;
      delay(2);
    }
    else
    {
      SERIAL_PORT.println("Waiting for data");
      delay(500);
    }

  }
  Counter = Counter + 1;
  SendMsg("PL", Counter);
  SendMsg("PT", millis());
  myLog.println("Counter: " + String(Counter));
  myLog.println("Time: " + String(millis()));

  J = 0;
  myLog.println(" ");
  myLog.print(Counter);
  myLog.println(" ");

}