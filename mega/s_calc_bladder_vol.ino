// The sketch calculates the GAS and BLADDER volumes

void CalcBladderVol()
{
  myMux.begin(TopMux);

  ReadTemp(0);
  float AccTemp = TempSensor.temperature() - 1.3;
  SendMsg("AT", AccTemp);

  ReadPress(1);
  float AccPress = PresSensor.pressure() - 10;
  SendMsg("AP", AccPress);

  GasVol = P1 * V1 * (AccTemp + 273.15) / (AccPress * 0.987 / 1000.0) / T1 / 0.9277 - 0.016;
  BladdVol = GasVol - V1;

  //SendMsg("BV", BladdVol);
}
