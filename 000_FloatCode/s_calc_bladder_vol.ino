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

  GasVol = P1 * V1 * (AccTemp + 273.15) / (AccPress * 0.987 / 1000.0) / T1;
  BladdVol = (GasVol - 642);

  SendMsg("BV", BladdVol);

  if (BladdVol <= (BladderLowerLimit + BladderBuffer))
  {
    BF = 1;
  }

  else if (BladdVol >= (BladderUpperLimit - BladderBuffer))
  {
    BF = 2;
  }

  else
  {
    BF = 0;
  }

  SendMsg("BF", BF);
}