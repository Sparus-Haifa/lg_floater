#include <LowPower.h> // https://github.com/rocketscream/Low-Power

//-=-=-=-=-=-=-=-=-=-=-=-=-= Pins allocation
// On NANO pins 3, 5, 6, 9, 10, 11 are PWM pins 490 Hz (pins 5 and 6: 980 Hz)

#define WakeUpPin     3  // On NANO, pin D2 and D3 are interupt enabled pins
#define MotorPin      2
#define DirectionPin  6

//-=-=-=-=-=-=-=-=-=-=-=-=-= COMMS
float outMsg[3], inMsg[1];
char OutgoingIdentifier[2];

//-=-=-=-=-=-=-=-=-=-=-=-=-= FLAGS
int DropWeightFlag = 0;

//-=-=-=-=-=-=-=-=-=-=-=-=-= GENERAL
unsigned long PreviousMillisIn = 0, PreviousMillisOut = 0;
unsigned long HBwait = 8000; // Wait time (in milliseconds)
unsigned long MotorTime = 8000; // Duration of DW motor actuation

bool rpiIsAlive = false;
int graceTime = 5000;
