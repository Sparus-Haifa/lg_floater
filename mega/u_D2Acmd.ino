// The function passes the desired pump command voltage in %
// as a 12bit value.

void D2Acmd(float Vval)
{
  float vv = Vval * 4095.0 / 100.0;
  Serial.println(vv);
  Wire.beginTransmission(MCP4725_ADDR);
  Wire.write(64);             // cmd to update the DAC
  Wire.write(int(vv) >> 4);        // the 8 most significant bits...
  Wire.write((int(vv) & 15) << 4); // the 4 least significant bits...
  Wire.endTransmission();
}
