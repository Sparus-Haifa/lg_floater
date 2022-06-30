//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= SETUP
void setup()
{
  //-=-=-=-=-=-=-=-=-=-=-=-=-= PINS SETUP
  pinMode(PumpDirectionPin, OUTPUT);
  pinMode(RPMReadPin, INPUT);
  pinMode(ValvePin, OUTPUT);
  pinMode(MainRelayPin, OUTPUT);
  pinMode(DropDown12VEnable, OUTPUT);
  pinMode(LightPin, OUTPUT);
  pinMode(HullLeakPin, INPUT);
  pinMode(VBEoutPin, OUTPUT);

  Serial.begin(115200);
  //Serial.setTimeout(2000);

  Wire.begin();   // Start I2C comm

  delay(500);
  SendMsg("SU", 0);

  //-=-=-=-=-=-=-=-=-=-=-=-=-= PUMP INIT.
  D2Acmd(0);  // stop the pump

  //-=-=-=-=-=-=-=-=-=-=-=-=-= engage main battery
  digitalWrite(MainRelayPin, HIGH); // enable main relay

  //-=-=-=-=-=-=-=-=-=-=-=-=-= LIGHT SIGNAL = START OF SETUP
  digitalWrite(LightPin, HIGH); // turn light on

  digitalWrite(ValvePin, LOW);    // close the valve

  //-=-=-=-=-=-=-=-=-=-=-=-=-= WATCHDOG TIMER INIT
  // enable the watchdog timer to reset at least every X seconds
  // possible values 0.5/1/2/4/8 seconds

  wdt_enable(WDTO_4S);

  //wdt_disable(); // disable the watchdog timer

  //-=-=-=-=-=-=-=-=-=-=-=-=-= SENSOR SETUP

  //Wire.setClock(400000); //Set I2C data rate to 400kHz

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= MUX SETUP
  // BOTTOM MUX
  //InitMUX(BottomMux);

  // TOP MUX
  InitMUX(TopMux);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= BOTTOM MUX SENSORS
  myMux.begin(BottomMux);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= BOTTOM TEMP

  InitTemp(0);
  SensorsBottom[0] = TempSensor.temperature();
  SendMsg("BT1", SensorsBottom[0]);

  InitTemp(1);
  SensorsBottom[1] = TempSensor.temperature();
  SendMsg("BT2", SensorsBottom[1]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= BOTTOM PRESS

  InitPress(2);
  SensorsBottom[2] = PresSensor.pressure();
  SendMsg("BP1", SensorsBottom[2]);

  InitPress(3);
  SensorsBottom[3] = PresSensor.pressure();
  SendMsg("BP2", SensorsBottom[3]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= HYDRAULIC PRESS
  InitPress(4);
  SensorsBottom[4] = PresSensor.pressure();
  SendMsg("HP", SensorsBottom[4]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= TOP MUX SENSORS
  myMux.begin(TopMux);
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= ACCUMULATOR SENSORS
  InitTemp(0);
  SensorsTop[0] = PresSensor.temperature();
  SendMsg("AT", SensorsTop[0]);

  InitPress(1);
  SensorsTop[1] = PresSensor.pressure();
  SendMsg("AP", SensorsTop[1]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= TOP TEMP
  InitTemp(2);
  SensorsTop[2] = PresSensor.temperature();
  SendMsg("TT1", SensorsTop[2]);

  InitTemp(4);
  SensorsTop[4] = PresSensor.temperature();
  SendMsg("TT2", SensorsTop[4]);

  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= TOP PRESS
  InitPress(3);
  SensorsTop[3] = PresSensor.pressure();
  SendMsg("TP1", SensorsTop[3]);

  InitPress(5);
  SensorsTop[5] = PresSensor.pressure();
  SendMsg("TP2", SensorsTop[5]);

  Serial.println("");

  //-=-=-=-=-=-=-=-=-=-=-=-=-= BNO080 IMU
  myIMU.begin();
  myIMU.enableLinearAccelerometer(1000); //Send data update every 500ms

  if (myIMU.dataAvailable() == true)
  {
    X_acc = myIMU.getLinAccelX();
    Y_acc = myIMU.getLinAccelY();
    Z_acc = myIMU.getLinAccelZ();
    SendMsg("X", X_acc);
    SendMsg("Y", Y_acc);
    SendMsg("Z", Z_acc);
  }

  //-=-=-=-=-=-=-=-=-=-=-=-=-= BR Ping

  pingSerial.begin(115200);

  while (!ping.initialize())
  {
    delay(500);
    PingDistance = ping.distance();
    PingConfidence = ping.confidence();
    SendMsg("D", PingDistance);
    SendMsg("C", PingConfidence);
  }

  //  //-=-=-=-=-=-=-=-=-=-=-=-=-= GPS/IRIDIUM BEACON
  //  // Wires: Black = GND, Orange = 5V, White = TX2, Green = RX2
  if (myI2CGPS.begin() == false)
  {
    SendMsg("GPS", 0);
  }

  GPS_getTime();

  IridiumSerial.begin(19200);
  // Assume battery power
  modem.setPowerProfile(IridiumSBD::DEFAULT_POWER_PROFILE);

  // Setup the Iridium modem
  if (modem.begin() != ISBD_SUCCESS)
  {
    SendMsg("IRID", 0);
  }

  //-=-=-=-=-=-=-=-=-=-=-=-=-= END OF SETUP
  //-=-=-=-=-=-=-=-=-=-=-=-=-= LIGHT SIGNAL OFF = END OF SETUP
  delay(1000);
  digitalWrite(LightPin, LOW); // turn light on
  SendMsg("SU", 1);
}
