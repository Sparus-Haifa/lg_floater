// This sketch initializes the Pressure sensor and reads the meassured value

void InitPress(byte port)
{
  myMux.setPort(port);
  myMux.enablePort(port);
  while (!PresSensor.init()) {
    Serial.println("Init failed!");
    Serial.println("Are SDA/SCL connected correctly?");
    Serial.println("Blue Robotics Bar30: White=SDA, Green=SCL");
    Serial.println("\n\n\n");
    delay(1000);
  }
  PresSensor.read();
  myMux.disablePort(port);
}
