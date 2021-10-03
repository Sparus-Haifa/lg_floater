void LinearAccelerometer()
{
  X_acc = myIMU.getLinAccelX();
  Y_acc = myIMU.getLinAccelY();
  Z_acc = myIMU.getLinAccelZ();
  LinAccuracy = myIMU.getLinAccelAccuracy();
}
