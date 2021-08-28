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
  BladdVol = (GasVol - V1) * 1.0728 - 5.34;

  if (BladdVol <= (BladderLowerLimit + BladderBuffer))
  {
    SendMsg("BF", 1);
  }

  else if (BladdVol >= (BladderUpperLimit - BladderBuffer))
  {
    SendMsg("BF", 2);
  }

  else
  {
    SendMsg("BF", 0);
  }
}
