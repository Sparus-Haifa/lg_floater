import pyduinocli
import json
import sys
from glob import glob

class ArduinoBurner:
    def __init__(self) -> None:
        self.arduino_cli = pyduinocli.Arduino("/home/pi/lg_floater/bin/arduino-cli")

    def getList(self):
        return self.arduino_cli.board.list()['result']

    def getVersion(self):
        return self.arduino_cli.version()


    def burnMega(self, address: str):
        # sketch_path = '/home/pi/lg_floater/TestSketch'
        sketch_path = '/home/pi/lg_floater/000_FloatCode'
        libraries_path = '/home/pi/lg_floater/000_FloatCode/libraries/*/'
        fqbn = 'arduino:avr:mega'
        libraries = glob(libraries_path)
        # self.arduino_cli.lib.install(libraries=libraries_path)
        res = self.arduino_cli.compile(sketch_path, fqbn=fqbn, library=libraries)
        print(res)
        stdout = res['__stdout']
        stdout_dict = json.loads(stdout)
        compiler_out = stdout_dict['compiler_out']
        print(compiler_out)
        compiler_err = stdout_dict['compiler_err']
        print(compiler_err)
        success = stdout_dict['success']


        stderr = res['__stderr']
        # print(stderr)

        # test compilation
        if not success:
            print('compilation failure')
            print(stderr)
            exit(1)


        builder_result = stdout_dict['builder_result']
        build_path = builder_result['build_path']
        
    
        
        # upload bin to arduino
        try:
            self.arduino_cli.upload(sketch_path, fqbn=fqbn, input_dir=build_path, port=address, verify=True)
        except pyduinocli.ArduinoError as e:
            print(e)
            exit(1)
        # print(res)


    def burnNano(self, address: str):
        # sketch_path = '/home/pi/lg_floater/nano'
        # sketch_path = '/home/pi/lg_floater/TestSketch'
        sketch_path = '/home/pi/lg_floater/000_NanoCode'
        libraries_path = '/home/pi/lg_floater/000_NanoCode/libraries/*/'
        libraries = glob(libraries_path)
        fqbn = "arduino:avr:nano"
        print('sketch_path', sketch_path)
        res = self.arduino_cli.compile(sketch_path, fqbn=fqbn, library=libraries)
        # print(res)

        stdout = res['__stdout']
        # print(res)
        stdout_dict = json.loads(stdout)
        # print(d)
        compiler_out = stdout_dict['compiler_out']
        print(compiler_out)
        compiler_err = stdout_dict['compiler_err']
        print(compiler_err)
        success = stdout_dict['success']

        stderr = res['__stderr']


        # test compilation
        if not success:
            print('compilation failure')
            print(stderr)
            exit(1)


        builder_result = stdout_dict['builder_result']
        build_path = builder_result['build_path']
        
    
        
        # upload bin to arduino
        try:
            self.arduino_cli.upload(sketch_path, fqbn=fqbn, input_dir=build_path, port=address, verify=True)
        except pyduinocli.ArduinoError as e:
            print(e)
            exit(1)
        # print(res)



def main():

    burner = ArduinoBurner()
    board_list = burner.getList()

    print(board_list)

    # # print(board_list)
    # for board in board_list:
    #     address = board['port']['address']
    #     protocol_label = board['port']['protocol_label']
    #     properties = board['port'].get('properties',None)  # ]['serialNumber']
    #     if properties is None:
    #         continue

    #     serialNumber = properties['serialNumber']
    #     print(address, protocol_label, serialNumber)


    #     if serialNumber == 'AH06F1J3' or serialNumber == 'AK08KITO':
    #         print(f'Arduino NANO was found on adress {address}')
    #         burner.burnNano(address)
        
    #     elif serialNumber == '85731303533351B0E1B2':
    #         print(f'Arduino MEGA was found on adress {address}')
    #         burner.burnMega(address)

    #     else:
    #         print(f'skipping board {serialNumber}')

    mega_address = '/dev/ttyACM0'
    burner.burnMega(mega_address)

    nano_address = '/dev/ttyUSB0'
    burner.burnNano(nano_address)
            

if __name__=='__main__':
    main()