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

  // Filling at full bladder
  GasVol = P1 * V1 * (AccTemp + 273.15) / (AccPress * 0.987 / 1000.0) / T1;
  BladdVol = GasVol - 1430 + 725 - 10; // correction of -10 
  BladdVol = BladdVol*1.311 - 8.6623; // Correction from filling test

  // Filling at empty bladder
  //  GasVol = P1 * V1 * (AccTemp + 273.15) / (AccPress * 0.987 / 1000.0) / T1;
  //  BladdVol = GasVol - V1;


  //BladdVol = 1.0215 * BladdVol; // - 50.92;

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
