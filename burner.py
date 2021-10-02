import pyduinocli
import json

class ArduinoBurner:
    def __init__(self) -> None:
        self.arduino_cli = pyduinocli.Arduino("/home/pi/lg_floater/bin/arduino-cli")

    def getList(self):
        return self.arduino_cli.board.list()['result']

    def getVersion(self):
        return self.arduino_cli.version()


    def burnNano(self, address: str):
        # sketch_path = '/home/pi/lg_floater/nano'
        sketch_path = '/home/pi/lg_floater/TestSketch'
        fqbn = "arduino:avr:nano"
        print('sketch_path', sketch_path)
        res = self.arduino_cli.compile(sketch_path, fqbn=fqbn)
        # print(res)

        res = res['__stdout']
        # print(res)
        dict_res = json.loads(res)
        # print(d)
        compiler_out = dict_res['compiler_out']
        print(compiler_out)
        compiler_err = dict_res['compiler_err']
        print(compiler_err)
        success = dict_res['success']

        # test compilation
        if not success:
            print('compilation failure')
            exit(1)


        builder_result = dict_res['builder_result']
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

    # print(board_list)
    for board in board_list:
        address = board['port']['address']
        protocol_label = board['port']['protocol_label']
        properties = board['port'].get('properties',None)  # ]['serialNumber']
        if properties is None:
            continue

        serialNumber = properties['serialNumber']
        # print(address, protocol_label, serialNumber)


        if serialNumber == 'AH06F1J3':
            print(f'Arduino NANO was found on adress {address}')
            burner.burnNano(address)


if __name__=='__main__':
    main()