#include <LowPower.h>       // https://github.com/rocketscream/Low-Power

//-=-=-=-=-=-=-=-=-=-=-=-=-= Pins allocation
// On NANO pins 3, 5, 6, 9, 10, 11 are PWM pins 490 Hz (pins 5 and 6: 980 Hz)

#define WakeUpPin     3  // On NANO, pin D2 and D3 are interupt enabled pins
#define MotorPin      6
#define DirectionPin  2

//-=-=-=-=-=-=-=-=-=-=-=-=-= COMMS
float outMsg[3], inMsg[1];
char OutgoingIdentifier[2];

//-=-=-=-=-=-=-=-=-=-=-=-=-= FLAGS
int DropWeightFlag = 0, LoopFlag = 0;

//-=-=-=-=-=-=-=-=-=-=-=-=-= GENERAL
unsigned long PreviousMillisIn = 0, PreviousMillisOut = 0;
#define HBwait  15000      // Wait time (in milliseconds)
#define MotorTimeHigh  30000   // Duration of DW motor actuation
#define MotorTimeLow   32000   // Motor speed is lower in this direction

bool rpiIsAlive = false;
int graceTime = 5000;
