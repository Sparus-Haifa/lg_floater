
/* This scetch is the control algorithm of the Haifa Uni Lagrangian Float
    Written by: Yuri Katz, 21/12/2020.
    The scetch is divided into tabs: PreSetup, Setup, void loop, followed by the various functions
    in the order they are called by the main scetch: MUX, Sensors, Pump_Control, Ping etc.

    In addition to the notes this tab includes the constants that might be of interest
    to the user to review/change.

    The transmission data is colon ":" seperated, the string is formatted as follows:

   ----------- SETUP ------------------
   At setup start will be sent SU:0
   At setup end will be sent   SU:1

   ----------- STANDARD LOOP OUTGOING SENSORS DATA ------------------

    1. BT1 - Bottom Temp 1
    2. BT2 - Bottom Temp 2
    3. BP1 - Bottom Press 1
    4. BP2 - Bottom Press 2
    5. HP - Hydraulic Press
    5. TT1 - Top Temp 1
    6. TT2 - Top Temp 2
    7. TP1 - Top Press 1
    8. TP2 - Top Press 2
    9. AT - Accumulator Temp
   10. AP - Accumulator Press
   11. BV - Bladder Volume
   12. X - IMU X axis
   13. Y - IMU Y axis
   14. Z - IMU Z axis
   15. PD - Altimeter Depth
   16. PC - Altimeter Confidance
  
   ------------  TIME ON (PUMP ON) CYCLE
   Once Arduino receives the 3 required inputs to actuate the pump: 
   Voltage "V":[40-100], Time On "T":[0.5-5], Pumping Direction "D":[1,2]
   the pump is turned on. The Arduino monitors the Pump RPM to verify that 
   the pump succeded to start. If the pump failed to start the Arduino will 
   retry X times (X from config file, currently 3 tries) to restart the pump.
   If the pump starts the Arduino will return the pump flag "PF":0/1 for each try.
   If the pump fails to start the preset X times, Ard will return "PF":2 for pump failure.
   At "PF":2 RPi will initiate emergency surfacing = droping the dropweight.
   
   While pump is engaged the following data is transmitted every function cycle
   (Standard data (1-16) is paused)

  17. RPM - Pump RPM
  and BV - Bladder Volume

  When pump is turned OFF, whether due to time elapsed or reaching MAX/MIN bladder boundery
  Ard will return "PF":0.

    ----------- OUTGOING FLAGS  ----------------------
    19. HL - Hull Leak (0/1) !!SAFETY!! Sent Every Ard loop
    20. EL - VBE Leak (0/1)  !!SAFETY!! Sent Every Ard loop
    21. FS:1 - FULL SURFACE INITIATED - Sent only when initiated 
    IF A LEAK IS DETECTED ARD WILL INITIATE FULL SURFACE AND INFORM RPi TO DROP WEIGHT

    BEACON FUNCTION:
    21. GE: 0/1 - 0 = NO GPS FIX / 1 = GPS OK
    22. IE: 0/XX - IRIDIUM ERROR #XX / 0 = IRIDIUM OK
    
    ----------- INCOMING DATA AND FLAGS -----------------------------

      The received transmission is formatted as follows:
   1. V: xx - Pump voltage in %, between 40 and 100
   2. T: x.x - Pump Time in sec (Between 0.5 and 5 sec)
   3. D: (1/2) - Pump direction: 1 = pump into Accumulator (GO DOWN) / 2 = pump into Bladder (GO UP)
   4. L: x - Signal light: Some light signals
   5. I: (0/1) - start/stop GPS/Iridium beacon at the surface (when Air is identified, same as WATER ID at mission start)
   6. E: (0/1) - Initiate emergency surface (due to NANO failure)

  ------------------------ SAFETY -----------------------------------
  Ping (altimeter): 
  IF DISTANCE SMALLER THAN CRITICAL RPi DROPS WEIGHT
  PD:xx.xx - distance, the distance is provided native in mm, translated to meters before transmition to RPi
  PC:xx.xx - confidance, a meassure of the accuracy of the distance
  
  OPTION - if distance from bottom is Smaller than YELLOW THRESHOLD (from config file) RPi Should inflate bladder to XXX cc 
  or Abort mission without droping weight.
  OPTION - IF CONFIDANCE IS BELOW RED THRESHOLD THE DISTANCE READING SHOULD BE DISREGARDED
*/
