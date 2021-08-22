//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= VOID LOOP

void loop()
{
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= RECEIVE INCOMING DATA
  ReceiveMsg();

  if (DropWeightFlag == 1)  // 1 = ALL OK signal
  {
    PreviousMillisIn = millis();
    SendMsg("NN", 1);        // 1 = ALL OK signal
    DropWeightFlag = 0; // Z
    rpiIsAlive = true;
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
    rpiIsAlive = false;
  }

  // if the heartbeat didn't arrive in time
  if (rpiIsAlive == false && (millis() - PreviousMillisIn) > HBwait + graceTime)
  {

    SendMsg("NN", 4); // 4 = weight dropped due to over time
    SendMsg("NN", millis());
    SendMsg("NN", PreviousMillisIn);
    SendMsg("NN", HBwait);
    
    RunMotor();
    

    
    delay(1000);
    Sleep();
  }
}

//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= END of VOID LOOP
