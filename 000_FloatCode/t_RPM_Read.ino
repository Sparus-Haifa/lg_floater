/*
  The pin marked as ‘RPM Pulse Output’ provides a frequency output (Hz) this can be measured
  with an oscilloscope. Some multimeters also have the ability to ready frequency.
  Connect the ‘RPM Pulse Output pin’ to an oscilloscope probe and the ground from the probe to
  the ground on the three pin header, this will display as a square waveform in which frequency
  can be read.
  For the correct RPM the read frequency must be multiplied by 10.
  Example 1000Hz x 10 = 10000 RPM.
  The MG2000 series will be at approximately 5500 RPM at full speed.
*/

float RPMRead()
{
  //int timeout = 500; // the number of microseconds to wait for the pulse to start
  float OnT = pulseIn(RPMReadPin, HIGH); //, timeout);
  float OffT = pulseIn(RPMReadPin, LOW); //, timeout);
  float period = OnT + OffT;
  // pulseIn returns the time in micro seconds
  float freq = 1000000.0 / period;
  float RPM = freq * 10;
  return RPM;
}
