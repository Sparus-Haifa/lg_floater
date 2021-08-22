// This sketch initializes the Pressure sensor and reads the meassured value

void ReadPress(byte port)
{
  myMux.setPort(port);
  myMux.enablePort(port);
  PresSensor.init();
  PresSensor.read();
  myMux.disablePort(port);
}
