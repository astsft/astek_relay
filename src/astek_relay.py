import sys
sys.path.append('../lib')

import traceback
import os
from configparser           import ConfigParser
import pymodbus.client as ModbusClient
from pymodbus.constants     import Endian
from pymodbus.payload       import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus import ( ExceptionResponse, Framer, ModbusException, pymodbus_apply_logging_config, )
#import asyncio



###############################################################################
# CALLBACK
class AstekRelay:

    def __init__(self, port, baud=19200, addr=0):
        self.port   = port
        self.baud   = baud
        self.addr   = addr
        self.client = ModbusClient.ModbusSerialClient(
            self.port,
            #framer=Framer.RTU,
            #framer=ModbusRtuFramer,
            timeout=1,
            retries=3,
            retry_on_empty=False,
            # strict=True,
            baudrate=self.baud,
            # bytesize=8,
            # parity="N",
            # stopbits=1,
            # handle_local_echo=False,
        )

    ###########################################################################
    # CLOSE
    def close( self ):
        self.client.close()

    ###########################################################################
    # SET STATE
    def get_state( self, chnl ):
        if   chnl in (0, '0', 'a', 'A'): addr = 0x0000
        elif chnl in (1, '1', 'b', 'B'): addr = 0x0001
        else: return None
        resp = self.client.read_coils( addr, 1, slave=self.addr ) 
        if resp.isError():
            return None
        #self.client.bit_read_message.ReadCoilsResponse
        #print( resp )
        return resp

    def set_state( self, chnl, state ):
        if   chnl in (0, '0', 'a', 'A'): addr = 0x0000
        elif chnl in (1, '1', 'b', 'B'): addr = 0x0001
        else:
            return None
        err = self.client.write_coil( addr, state, slave=self.addr )
        return err


    ###########################################################################
    # GET INFO
    def get_info( self ):
        connected = self.client.connect()
        if( connected ):
            try:
                #rr = self.client.read_holding_registers( 0, 32, slave=self.modbus_addr)
                rr = self.client.read_holding_registers( 0, 2, slave=self.modbus_addr)
                '''
                print( 'rr type: ', type(rr) )
                if rr.isError():
                    #data    = None
                    return rr
                else:
                    data = rr
                    obj     = BinaryPayloadDecoder.fromRegisters(raw.registers, byteorder=Endian.Big)
                    data    = { 'DEVICE ID':        obj.decode_16bit_uint(),
                            'HARDWARE ID':      obj.decode_16bit_uint(),
                            'RESERVED':         obj.skip_bytes(14*2),
                            'SERIAL NUM, HI':   obj.decode_64bit_uint(),
                            'SERIAL NUM, LO':   obj.decode_64bit_uint(),
                            #'SERIAL NUMBER':    obj.decode_string(8),
                            'RESERVED':         obj.skip_bytes(16),
                        }
                '''
            except ModbusException as exc:
                #raise exc
                print('ModbusException: ', exc)

        self.client.close()

        #print(opened)
        #if not opened:
        #    return False

        return connected
    ###########################################################################
    # GET INFO
    def scan( self ):
        for baud in (19200, 115200):
            for addr in (48, 49, 50, 51, 52, 53, 54, 55):
                print( '%s @ %i %i: ' % (self.port, baud, addr), end='' )
                try:
                    self.client = ModbusClient.ModbusSerialClient(
                        self.port,
                        #framer=Framer.RTU,
                        #framer=ModbusRtuFramer,
                        timeout=1,
                        retries=3,
                        retry_on_empty=False,
                        # strict=True,
                        baudrate=baud,
                        # bytesize=8,
                        # parity="N",
                        # stopbits=1,
                        # handle_local_echo=False,
                    )
                    connected = relay.client.connect()
                    if( connected ):
                        rr = relay.client.read_holding_registers( 0, 2, slave=addr)
                        relay.client.close()
                except ModbusException as exc:
                    print( exc )

                if not rr.isError():
                    print('OK')
                    #relay.client.close()
                    self.baud   = baud
                    self.addr   = addr
                    return baud, addr
                else:
                    print('ERROR')

                if isinstance(rr, ExceptionResponse):
                    print(f"Received Modbus library exception ({rr})")
                    # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
                    relay.client.close()

        return 0, 0


###############################################################################
# MAIN
if __name__ == '__main__':
    from os import system, name
    import time

    name, _     = os.path.splitext(os.path.basename(__file__))
    cp          = ConfigParser()
    cp.read( name + '.ini' )
    port        = cp.get(     'MODBUS',   'port'      )

    relay = AstekRelay(port)
    print('Scanning for Modbus address...')
    baud, addr = relay.scan()
    if addr != 0:
        print('\r\nRun test sequence...')
        try:
            while( True ):
                for chnl in range(2):
                    for state in range(2):
                        err = relay.set_state( chnl, state )
                        print(('CH_%d: %d\t') % (chnl, state), err, end='' )
                        resp = relay.get_state( chnl )
                        if resp != None:    print( resp )
                        else:               print()

                        time.sleep(1)
        except KeyboardInterrupt:
            print('\n\rExit...')
        except Exception:
            traceback.print_exc(file=sys.stdout)
    sys.exit(0)
