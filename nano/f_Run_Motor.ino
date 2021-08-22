void RunMotor()
{
  digitalWrite(DirectionPin, HIGH);
  analogWrite(MotorPin, 255);
  delay(MotorTime);
  analogWrite(MotorPin, 0);
  delay(500);

  digitalWrite(DirectionPin, LOW);
  analogWrite(MotorPin, 255);
  delay(MotorTime);
  analogWrite(MotorPin, 0);
}
