void InitMUX(byte MUXadrs)
{
  if (myMux.begin(MUXadrs) == false)
  {
    Serial.println("Top Mux not detected. Freezing...");
    while (1);
  }

  //  Serial.println("Top Mux detected");
  //  currentPortNumber = myMux.getPort();
  //  Serial.print("Top Mux Current Port: ");
  //  Serial.println(currentPortNumber);
}
