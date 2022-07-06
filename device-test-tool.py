import sys
import glob
import serial
import time

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def open_port(port,baudrate,parity):
    return serial.Serial(port=port,baudrate=baudrate,parity=parity)

def send_str(port_set, baudrate, parity, value):
    return port_set.write(value)

def read_str(port_set,wait_time):
    time.sleep(wait_time)
    return port_set.read_all()

def run_test_graph():
    global_data=dict()
    test_graph=[{'type':'init_com','id':'0','in':''},{'type':'test_node','id':'0','inDev':'$1'}]
    for i in test_graph:
        for key,value in i.items():
            print(key,":",value)

if __name__ == '__main__':
    ports = serial_ports()
    print(ports)
    # 020000001c800000001200003c0000be990000000c5000000000d10386070080908a03
    beginData=bytes([0x02,0x00,0x00,0x00,0x1c,0x80,0x00,0x00,0x00,0x12,0x00,0x00,0x3c,0x00,0x00,0xbe,0x99,0x00,0x00,0x00,0x0c,0x50,0x00,0x00,0x00,0x00,0xd1,0x03,0x86,0x07,0x00,0x80,0x90,0x8a,0x03])
    # or 
    # beginData=b'\x02\x00\x00\x00\x1c\x80\x00\x00\x00\x12\x00\x00\x3c\x00\x00\xbe\x99\x00\x00\x00\x0c\x50\x00\x00\x00\x00\xd1\x03\x86\x07\x00\x80\x90\x8a\x03'
    # if 'COM3' in ports:
    #     result=send_str('COM3',115200,'N',beginData)
    #     for i in result:
    #         print(i)
    
    run_test_graph()