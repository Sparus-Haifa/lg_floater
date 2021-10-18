// This sketch initializes the Temperature sensor and reads the meassured value

void InitTemp(byte port)
{
  myMux.setPort(port);
  myMux.enablePort(port);
  TempSensor.init();
  TempSensor.read();
  myMux.disablePort(port);
}
