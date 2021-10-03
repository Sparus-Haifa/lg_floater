// This sketch sends a floay value to the RPi with a preagreed  ID code, seperated by :

void SendMsg(char id[2], float msg)
{
  Serial.print(id);
  Serial.print(":");
  Serial.println(msg);
}
