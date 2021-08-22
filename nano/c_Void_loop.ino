//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= VOID LOOP

void loop()
{
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= RECEIVE INCOMING DATA
  ReceiveMsg();

  if (DropWeightFlag == 1)  // 1 = ALL OK signal
  {
    PreviousMillisIn = millis();
    SendMsg("NN", 1);        // 1 = ALL OK signal
  }

  else if (DropWeightFlag == 2) // 2 = the command to drop the dropweight
  {
    SendMsg("NN", 2);
    RunMotor();
    delay(1000);
    Sleep();
  }

  // send outgoing Heart Beat every 20 seconds
  if ((millis() - PreviousMillisOut) > HBwait / 2)
  {
    PreviousMillisOut = millis();
    SendMsg("NN", 3);
  }

  // if the heartbeat didn't arrive in time
  if ((millis() - PreviousMillisIn) > HBwait)
  {
    RunMotor();
    SendMsg("NN", 4); // 4 = weight dropped due to over time
    delay(1000);
    Sleep();
  }
}

//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= END of VOID LOOP
