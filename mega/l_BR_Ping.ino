/*
    This example is targeted toward the arduino platform

    This example demonstrates the most simple usage of the Blue Robotics
    Ping1D c++ API in order to obtain distance and confidence reports from
    the device.

    This API exposes the full functionality of the Ping1D Echosounder

  Communication is performed with a Blue Robotics Ping1D Echosounder
  The serial port is used to communicate with the Ping device
  arduino rx (Ping tx, white), arduino tx (Ping rx, green)
*/

//struct PingData 
void AltPing()
{
  //struct PingData PingDF;
  if (ping.update())
  {
    PingDistance = ping.distance();
    //  Serial.print("Distance: ");
    //   Serial.print(PingDF.distance);
    PingConfidence = ping.confidence();
    //  Serial.print("\tConfidence: ");
    // Serial.println(PingDF.confidence);
  }
  else
  {
    //Serial.println("No update received!");
    PingDistance = 0;
    PingConfidence = 0;
  }
  // Toggle the LED to show that the program is running
  //digitalWrite(ledPin, !digitalRead(ledPin));
 // return PingDF;
}
