void ReceiveMsg()
{
  while (Serial.available() > 0)
  {
   char IncomingIdentifier = Serial.read();
    switch (IncomingIdentifier)
    {
      // Case "N" - Cyclic heartbeat!!!
      case 'N': DropWeightFlag = Serial.parseInt();
        //      Serial.print("User message received: ");
        //      Serial.print(IncomingIdentifier);
        //      Serial.print(" | Value: ");
        //      Serial.println(inMsg[0]);
        break;

    }
  }
}
