void InitMUX(byte MUXadrs)
{
  if (myMux.begin(MUXadrs) == false)
  {
    SendMsg("MUX", MUXadrs);
    while (1);
  }
}
