// This sketch initializes the Pressure sensor and reads the meassured value

void InitPress(byte port)
{
  myMux.setPort(port);
  myMux.enablePort(port);
  while (!PresSensor.init()) {
    SendMsg("PS", port);
    delay(1000);
  }
  PresSensor.read();
  myMux.disablePort(port);
}
