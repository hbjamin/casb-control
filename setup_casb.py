#!/usr/bin/env python

import sys
import math
import time
import json
import subprocess

class DataLoader():
    def __init__(self,file):
        self.file=file
        self.masks=[]
        self.thresholds=[]
        self.width=[]

    def parse(self):
        with open(self.file, 'r') as f:
            data = json.load(f)
        self.masks=data['channel_masks'] 
        self.thresholds=data['comparator_thresholds']
        self.widths=data['comparator_widths']

    def validate(self):
        print("TODO: Validate")

    def print(self):
        print("CHANNEL MASKS:")
        for i in range(len(self.masks)):
            if self.masks[i]==0:
                print("CH",str(i+1)+": OFF")
            else:
                print("CH",str(i+1)+": ON")
        print("COMPARATOR THRESHOLDS:")
        print("    HIGH:",self.thresholds['high'])
        print("     MED:", self.thresholds['med'])
        print("     LOW:", self.thresholds['low'])
        print("     TOT:", self.thresholds['tot'])
        print("ATTN TOT:", self.thresholds['attn_tot'])
        print("COMPARATOR WIDTHS:")
        print("    HIGH:", self.widths['high'])
        print("     MED:", self.widths['med'])
        print("     LOW:", self.widths['low'])
        print("     TOT:", self.widths['tot'])
        print("ATTN TOT:", self.widths['attn_tot'])

    def getData(self):
        return self.masks,self.thresholds,self.widths

class CASB():
    def __init__(self,masks,thresholds,widths):   
        self.masks=masks
        self.thresholds=thresholds
        self.widths=widths
        self.dacAdcBus=0 #i2c
        self.regulatorBus=1 #i2c
        self.threshDacAddr=0x48 
        self.widthDacAddr=0x49
        self.boardIdAddr=0x50 #check this
        self.adcAddr=0x22 #check this
        self.regAddr=[0x43C00000,0x43C00004,0x43C00008,0x43C0000C] 
        self.threshDacRegMap={
            0:'unityBLR',
            1:'attnBLR',
            2:'high',
            3:'med',
            4:'low',
            5:'tot',
            6:'attn_tot'
        }
        self.widthDacRegMap={
            0:'high',
            1:'med',
            2:'low',
            3:'tot',
            4:'attn_tot'
        }

    def voltageToDac10bit(self,voltage):
        vref=3.3
        bits=10
        resolution=vref/(math.pow(2,bits))
        return round(voltage/resolution)
    
    def Dac10bitToVoltage(self,val):
        vref=3.3
        bits=10
        resolution=vref/(math.pow(2,bits))
        return round(val*resolution)
       
    def writeToDac(self,bus,dacAddr,temp,voltage):
        val=self.voltageToDac10bit(self.voltage)
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

    def readFromDac(self):
        # Command + Access byte
        read_ca=0x00+self.channel
        # Make shell command to run
        command=f"sudo i2cget -y {self.bus} {self.dac_address} {read_ca} i"  
        # Write data to DAC
        result=subprocess.run(command,shell=True,capture_output=True,text=True).stdout.strip()
        msb=int(result[0:4],16)
        lsb=int(result[5:9],16)
        val=((msb<<8)+lsb)>>6
        voltage=self.Dac10bitToVoltage(val)
        print("Reading ------------")
        print(f"    I2C BUS: {self.bus}")
        print(f"DAC ADDRESS: {hex(self.dac_address)}")
        print(f"    CHANNEL: {self.channel}")
        print(f"    VOLTAGE: {float(voltage)}")
        print(f"10b DAC VAL: {format(val,'#06x')} {format(val,'10b')}")
        print(f"        MSB: {format(msb,'#06x')} {format(msb,'08b')}")
        print(f"        LSB: {format(lsb,'#06x')} {format(lsb,'08b')}")
        time.sleep(0.01)

    def writeToMem(self):
        print("todo")

    def readFromMem(self):
        print("todo")

    def setMasks(self):
        print("todo")

    def setThresholds(self):
        print("todo")
    
    def setWidths(self):
        print("todo")

def main():

    if len(sys.argv)!=2:
        print("This script expects one argument: the CASB's json config file")
        sys.exit(1) 

    file = sys.argv[1]  

    loader=DataLoader(file)
    loader.parse()
    loader.validate()
    loader.print()
    masks,thresholds,widths=loader.getData() 

    casb=CASB(masks,thresholds,widths) 
    casb.setMasks()
    casb.setThresholds()
    casb.setWidths()

    #Then make loop that restores baseline

if __name__ == "__main__":
    main()


