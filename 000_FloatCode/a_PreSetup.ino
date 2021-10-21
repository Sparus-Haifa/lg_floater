//-=-=-=-=-=-=-=-=-=-=-=-=-= SIMULATION PARAMETERS !!!

//#define LeakNow 2  // TIME UNTIL LEAK IN MINUTES


//-=-=-=-=-=-=-=-=-=-=-=-=-= SIMULATION PARAMETERS !!!

// Libraries
#include <avr/wdt.h>
#include <Wire.h>
#include "TSYS01.h"                             // https://github.com/bluerobotics/BlueRobotics_TSYS01_Library
#include "MS5837.h"                             // https://github.com/bluerobotics/BlueRobotics_MS5837_Library
#include "SparkFun_BNO080_Arduino_Library.h"    // http://librarymanager/All#SparkFun_BNO080
#include "ping1d.h"                             // https://www.arduinolibraries.info/libraries/ping-arduino
#include <SparkFun_I2C_Mux_Arduino_Library.h>   // https://github.com/sparkfun/SparkFun_I2C_GPS_Arduino_Library
#include <TinyGPS++.h>                          // https://github.com/mikalhart/TinyGPSPlus
#include <SparkFun_I2C_GPS_Arduino_Library.h>   // https://github.com/sparkfun/SparkFun_I2C_GPS_Arduino_Library
#include <IridiumSBD.h>                         // https://github.com/sparkfun/SparkFun_IridiumSBD_I2C_Arduino_Library

//-=-=-=-=-=-=-=-=-=-=-=-=-= OBJECTS DEFINITIONS

// Declare MUX object
QWIICMUX myMux;  
#define BottomMux 0x70
#define TopMux    0x71

// MCP4725A0 D2A address 
#define MCP4725_ADDR 0x60 

// define GPS library object
I2CGPS myI2CGPS; 
TinyGPSPlus gps; //Declare gps object

// Define PING Altimeter object
#define pingSerial Serial1
static Ping1D ping { pingSerial };
float  PingDistance;
byte   PingConfidence;

// Temperature and Pressure sensors objects
TSYS01 TempSensor;
MS5837 PresSensor;

// IridiumSBD object
#define     IridiumSerial Serial2
IridiumSBD  modem(IridiumSerial);    // Declare IRIDIUM object
TinyGPSPlus tinygps;                // Declare TINY GPS object
static const int ledPin = LED_BUILTIN;

#define BEACON_INTERVAL 10         // Time between transmissions (seconds)
#define BeaconT 5                   // Duration of beacon function (minutes)

// IMU object
BNO080 myIMU;

//-=-=-=-=-=-=-=-=-=-=-=-=-= VARIABLES DECLARATIONS
bool PumpDirectionBool;
float PumpVoltage, PumpTime;
int PumpDirection, Duty, PumpRPM, BladderVolSetPoint, BladderBuffer = 10;
float Time, Freq, Period;

// COMMS
float outMsg[3], inMsg[1];
char OutgoingIdentifier[2], IncomingIdentifier;

float TempReading, PresReading, PressVBE;
float SensorsBottom[7], SensorsTop[7];
byte currentPortNumber;

//-=-=-=-=-=-=-=-=-=-=-=-=-= FLAGS
byte IridiumFlag = 0, VBEleakFlag = 0, FullSurfaceFlag = 0;
byte HullLeakFlag = 0, PumpFlag = 0, LightFlag = 0, BF = 0;

//-=-=-=-=-=-=-=-=-=-=-=-=-= BNO080 IMU
float X_acc, Y_acc, Z_acc;
byte LinAccuracy;

//-=-=-=-=-=-=-=-=-=-=-=-=-= VBE LEAK
#define LeakTH 50             // VBE leak detection threshold

//-=-=-=-=-=-=-=-=-=-=-=-=-= GENERAL
unsigned long PreviousMillis = 0, LoopCounter = 1;

//-=-=-=-=-=-=-=-=-=-=-=-=-= PINS ALLOCATION
#define RPMReadPin          22  // Digital motor RPM feedback pin
#define PumpDirectionPin     3  // Pump direction control pin
#define DropDown12VEnable   53  // 12V DropDown chip enable
#define ValvePin            52  // Cutoff valve command pin = Relay 1 enable
#define MainRelayPin        11  // Main Relay ON
#define LightPin            12  // Signal light control pin
#define VBEoutPin            7  // VBE leak detector voltage pin - not all Digital legs are PWM !!!
#define VBEinPin            A8  // VBE leak detector detector pin
#define HullLeakPin         50  // Hull Leak Signal Pin

//-=-=-=-=-=-=-=-=-=-=-=-=-= BLADDER PARAMETERS
// V1 = 0.7 L for accumulator full of oil, V1=1.4L for accumulator empty of oil
//float V1 = 1430 - 724;
float V1 = 1430;
float P1 = 6134 * (0.98692 / 1000.0);
float T1 = (273.15 + 23.55);
float GasVol, GasVolPrev, BladdVol;

// limits of the bladder volume in CC
#define BladderUpperLimit 620
#define BladderLowerLimit 30
