// This sketch reads the Temperature sensor
void ReadTemp(byte port)
{
  myMux.setPort(port);
  myMux.enablePort(port);
  //TempSensor.init();
  TempSensor.read();
  myMux.disablePort(port);
}
