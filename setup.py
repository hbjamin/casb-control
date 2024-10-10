import sys
import math
import time
import subprocess

class CASB_CONTROL():
    def __init__(self,channel,voltage):
        self.bus=0
        self.dac_address=0x48
        self.channel=channel
        self.voltage=voltage
        self.reg_address=[0x43C00000,0x43C00004,0x43C00008,0x43C0000C]
        self.writeToDAC()
        self.readFromDAC()
    
    def parseJSON(self,file):
        print("DO THIS")

    def voltageToDAC10bit(self,voltage):
        vref=3.3
        bits=10
        resolution=vref/(math.pow(2,bits))
        return round(voltage/resolution)
    
    def DAC10bitToVoltage(self,val):
        vref=3.3
        bits=10
        resolution=vref/(math.pow(2,bits))
        return round(val*resolution)
       
    def writeToDAC(self):
        val=self.voltageToDAC10bit(self.voltage)
        # Bitshift 6 to the left because we send 16bits to a 10bit DAC
        # and the DAC expects: msb lsb = [b9,b8,b7,b6,b5,b4,b3,b2] [b1,b0,x,x,x,x,x,x]
        dac_val=val<<6
        # Split ouput into most and least significant bytes
        msb=dac_val>>8
        lsb=dac_val%256 
        # Command + Access byte
        write_ca=0x30+self.channel
        # Shell command to run
        command=f"sudo i2cset -y {self.bus} {self.dac_address} {write_ca} {msb} {lsb} i"  
        print("Writing ------------")
        print(f"    I2C BUS: {self.bus}")
        print(f"DAC ADDRESS: {hex(self.dac_address)}")
        print(f"    CHANNEL: {self.channel}")
        print(f"    VOLTAGE: {self.voltage}")
        print(f"10b DAC VAL: {format(val,'#06x')} {format(val,'10b')}")
        print(f"        MSB: {format(msb,'#06x')} {format(msb,'08b')}")
        print(f"        LSB: {format(lsb,'#06x')} {format(lsb,'08b')}")
        # Write data to DAC
        subprocess.run(command,shell=True)
        time.sleep(0.01)

    def readFromDAC(self):
        # Command + Access byte
        read_ca=0x00+self.channel
        # Make shell command to run
        command=f"sudo i2cget -y {self.bus} {self.dac_address} {read_ca} i"  
        # Write data to DAC
        result=subprocess.run(command,shell=True,capture_output=True,text=True).stdout.strip()
        msb=int(result[0:4],16)
        lsb=int(result[5:9],16)
        val=((msb<<8)+lsb)>>6
        voltage=self.DAC10bitToVoltage(val)
        print("Reading ------------")
        print(f"    I2C BUS: {self.bus}")
        print(f"DAC ADDRESS: {hex(self.dac_address)}")
        print(f"    CHANNEL: {self.channel}")
        print(f"    VOLTAGE: {float(voltage)}")
        print(f"10b DAC VAL: {format(val,'#06x')} {format(val,'10b')}")
        print(f"        MSB: {format(msb,'#06x')} {format(msb,'08b')}")
        print(f"        LSB: {format(lsb,'#06x')} {format(lsb,'08b')}")
        time.sleep(0.01)


def main():
    if len(sys.argv)!=3:
        print("ERROR! 3 Arguments Required: <Channel#From0> <ThresholdVoltage>")
        sys.exit(1)
    casb=CASB_CONTROL(int(sys.argv[1]),float(sys.argv[2]))

if __name__=="__main__":
   main()
