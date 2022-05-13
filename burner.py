import pyduinocli
import json
import sys
from glob import glob
import serial.tools.list_ports


class ArduinoBurner:
    def __init__(self, log) -> None:
        self.arduino_cli = pyduinocli.Arduino("/home/pi/lg_floater/bin/arduino-cli")
        self.log = log

    def getList(self):
        return self.arduino_cli.board.list()['result']

    def getList_offline(self):
        ports = serial.tools.list_ports.comports()
        res = []
        for port, desc, hwid in sorted(ports):
                # print("{}: {} [{}]".format(port, desc, hwid))
                res.append((port, desc, hwid))
        return res


    def getVersion(self):
        return self.arduino_cli.version()


    def burnMega(self, address: str):
        self.log.info('compiling mega code')
        # sketch_path = '/home/pi/lg_floater/TestSketch'
        # sketch_path = '/home/pi/lg_floater/000_FloatCode'
        sketch_path = '/home/pi/lg_floater/000_FloatCode_sim'
        libraries_path = '/home/pi/lg_floater/000_FloatCode/libraries/*/'
        # fqbn = 'arduino:avr:mega'
        fqbn = 'arduino:avr:uno'
        libraries = glob(libraries_path)
        # self.arduino_cli.lib.install(libraries=libraries_path)
        print('compiling...')
        res = self.arduino_cli.compile(sketch_path, fqbn=fqbn, library=libraries)
        print('done')
        # print(res)
        # self.log.debug(res)
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
            self.log.critical('compilation failure')
            self.log.critical(stderr)
            exit(1)
        self.log.info('compilation successful')
        self.log.info('uploading mega code')



        builder_result = stdout_dict['builder_result']
        build_path = builder_result['build_path']
        
    
        
        # upload bin to arduino
        try:
            self.arduino_cli.upload(sketch_path, fqbn=fqbn, input_dir=build_path, port=address, verify=True)
        except pyduinocli.ArduinoError as e:
            self.log.critical(e)
            exit(1)
        # print(res)
        self.log.info('upload successful')


    def burnNano(self, address: str):
        self.log.info('compiling nano code')
        # sketch_path = '/home/pi/lg_floater/nano'
        # sketch_path = '/home/pi/lg_floater/TestSketch'

        sketch_path = '/home/pi/lg_floater/000_NanoCode'
        libraries_path = '/home/pi/lg_floater/000_NanoCode/libraries/*/'
        
        # sketch_path = 'C:\\nir\\lg_floater_async\\000_NanoCode\\000_NanoCode.ino'
        # libraries_path = 'C:\\nir\\lg_floater_async\\000_NanoCode\\libraries'
        
        libraries = glob(libraries_path)
        # fqbn = "arduino:avr:nano"
        fqbn = "arduino:avr:nano:cpu=atmega328old"
        print('sketch_path', sketch_path)
        res = self.arduino_cli.compile(sketch_path, fqbn=fqbn, library=libraries)
        # res = self.arduino_cli.compile(sketch_path, fqbn=fqbn)
        print(res)

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
            self.log.critical('compilation failure')
            self.log.critical(stderr)
            exit(1)
        self.log.info('compilation successful')
        self.log.info('uploading nano code')

        


        builder_result = stdout_dict['builder_result']
        build_path = builder_result['build_path']
        
    
        
        # upload bin to arduino
        try:
            self.arduino_cli.upload(sketch_path, fqbn=fqbn, input_dir=build_path, port=address, verify=True)
        except pyduinocli.ArduinoError as e:
            self.log.critical('upload failed')
            self.log.critical(e)
            exit(1)
        # print(res)
        self.log.info('upload successful')
        print('upload successful')

    def burn_boards(self):

        ports = self.getList_offline()
        open_ports = []
        for port, desc, hwid in sorted(ports):
            open_ports.append(port)


        mega_address = '/dev/ttyACM0'
        if mega_address not in open_ports:
            self.log.critical('mega board not found')
            exit(1)
        self.burnMega(mega_address)
        

        nano_address = '/dev/ttyUSB0'
        if nano_address not in open_ports:
            self.log.critical('nano board not found')
            exit(1)
        self.burnNano(nano_address)    



def main():


    # from lib.logger import Logger
    # logger = Logger(False)
    # log = logger.get_log()
    import logging
    log = logging.getLogger('burner')
    log.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log.addHandler(ch)
    log.debug('init')

    burner = ArduinoBurner(log)
    board_list = burner.getList_offline()

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
    # burner.burnNano("COM4")
            

if __name__=='__main__':
    main()