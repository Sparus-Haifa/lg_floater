/*  This sketch is for the Arduino Nano Dropweight controller. The sketch waits 
 *  for a heartbeat signal from the Pi every 30 seconds. If the signal is received on time
 *  then the timer is reset for another 30 seconds and the Nano returns an aknowledgement. 
 *  If not, then the dropweight is released and a message is sent to the Pi. 
 *  Also, the sketch is checking for an incoming active drop command. 
 *  The drop weight is released by actuating the motor via leg 2 for 10 seconds.  
 *  The NANO sends a heart beat to the Pi every 15 seconds
 *  
 *  The NANO is powered by a seperate battery, which can't be physically disconected. In
 *  order to conserve battery the NANO will be put to sleep at end of mission and awakened
 *  at start of mission. The WAKE-UP command will be given by pulling the connected Pi I/O
 *  pin to HIGH
 *  
 *  The incoming handshake header: N: 1 = OK / 2 = dropweight
 *  The outgoing handshake header: NN: 1 = OK / 2 = weight dropped due to command / 
 *  3 = NANO alive / 4 = weight dropped due to over time / 111 = NANO AWAKE / 222 = NANO ASLEEP
 */ 
