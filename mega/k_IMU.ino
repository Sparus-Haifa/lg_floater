void LinearAccelerometer()
{
  X_acc = myIMU.getLinAccelX();
  Y_acc = myIMU.getLinAccelY();
  Z_acc = myIMU.getLinAccelZ();
  LinAccuracy = myIMU.getLinAccelAccuracy();

//  Serial.print(x, 2);
//  Serial.print(F(","));
//  Serial.print(y, 2);
//  Serial.print(F(","));
//  Serial.print(z, 2);
//  Serial.print(F(","));
//  Serial.print(linAccuracy);
//  Serial.println();
}
