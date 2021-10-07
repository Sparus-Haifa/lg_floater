void ReceiveMsg()
{
  while (Serial.available() > 0)
  {
    char IncomingIdentifier = Serial.read();
    switch (IncomingIdentifier)
    {
      // Case "N" - Cyclic heartbeat!!!
      case 'N': DropWeightFlag = Serial.parseInt();
        //SendMsg("NN", DropWeightFlag); // HERE FOR DEBUGGING ONLY
        break;

      // Case "L" - Cyclic heartbeat!!!
      case 'L': LoopFlag = Serial.parseInt();
        //SendMsg("NN", DropWeightFlag); // HERE FOR DEBUGGING ONLY
        break;

    }
  }
}
