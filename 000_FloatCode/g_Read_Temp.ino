// This sketch reads the Temperature sensor
void ReadTemp(byte port)
{
  myMux.setPort(port);
  myMux.enablePort(port);
  TempSensor.read();
  myMux.disablePort(port);
}
