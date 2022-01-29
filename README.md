pip3.10 install -r .\requierments.txt


sudo apt-get update
sudo apt-get upgrade

curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
export PATH="/home/pi/lg_floater/bin/:$PATH"


arduino-cli core download arduino:avr
arduino-cli core install arduino:avr

arduino-cli board details arduino:avr:nano

arduino-cli board attach arduino:avr:nano:cpu=atmega328old /home/pi/lg_floater/000_NanoCode/

