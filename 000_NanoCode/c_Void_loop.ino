//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= VOID LOOP

void loop()
{
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= RECEIVE INCOMING DATA
  ReceiveMsg();

  while (LoopFlag == 0)
  {
    Sleep();
    delay(5000);

    ReceiveMsg();
    PreviousMillisOut = millis();
    PreviousMillisIn = millis();
  }

  // send outgoing Heart Beat every 20 seconds
  if ((millis() - PreviousMillisOut) >= HBwait)
  {
    PreviousMillisOut = millis();
    SendMsg("NN", 3);
    DropWeightFlag = 0;
    //rpiIsAlive = false;
  }

  if (DropWeightFlag == 1)       // 1 = ALL OK signal
  {
    PreviousMillisIn = millis(); // Reset incoming HB timer
    SendMsg("NN", 1);            // Acknowledge HB reception
    DropWeightFlag = 0;          // Reset the DropWeightFlag
    // rpiIsAlive = true;
  }

  if (DropWeightFlag == 2)       // 2 = the command to drop the dropweight
  {
    SendMsg("NN", 2);            // Acknowledge DROP command
    RunMotor();                  // Actuate DW motor
    delay(1000);
    Sleep();
    DropWeightFlag = 0;
  }

  // if the heartbeat didn't arrive in time
  if ((millis() - PreviousMillisIn) > HBwait + graceTime)
  {
    SendMsg("NN", 4);            // 4 = weight dropped due to over time
    RunMotor();
    delay(1000);
    Sleep();
    DropWeightFlag = 0;
  }

  if (DropWeightFlag == 5)       // 5 = go to sleep without dropping weight
  {
    SendMsg("NN", 5);            // Acknowledge DROP command
    delay(1000);
    Sleep();
    DropWeightFlag = 0;
  }
}
//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= END of VOID LOOP
