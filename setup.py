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
        print("------------------------")
        print("----- CONFIG FILE ------")
        print("------------------------")
        print("CHANNEL MASKS:")
        for i in range(len(self.masks)):
            if int(result[i])==1:
                print(f"CH {i+1:>2}: ON")
            else:
                print(f"CH {i+1:>2}: OFF")
        print("COMPARATOR THRESHOLDS:")
        print("   High:",self.thresholds['High'])
        print("    Med:",self.thresholds['Med'])
        print("    Low:",self.thresholds['Low'])
        print("    Tot:",self.thresholds['Tot'])
        print("AttnTot:",self.thresholds['AttnTot'])
        print("COMPARATOR WIDTHS:")
        print("   High:",self.widths['High'])
        print("    Med:",self.widths['Med'])
        print("    Low:",self.widths['Low'])
        print("    Tot:",self.widths['Tot'])
        print("AttnTot:",self.widths['AttnTot'])
        print("------------------------")

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
        self.regAddr=0x43C0000C 
        self.threshDacRegMap={
                 'BLR':0,
             'AttnBLR':1,
                'High':2,
                 'Med':3,
                 'Low':4,
                 'Tot':5,
             'AttnTot':6
        }
        self.widthDacRegMap={
                'High':0,
                 'Med':1,
                 'Low':2,
                 'Tot':3,
             'AttnTot':4
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
        return round(val*resolution,2)

    def printDacReadWrite(self,dacAddr,channel,ca,voltage,val,msb,lsb):
        if int(format(ca,'#04x')[2])==3:
            print(f"Writing ------------") 
        else:
            print(f"Reading ------------") 
        print(f"    I2C BUS: {self.dacAdcBus}")
        print(f"DAC ADDRESS: {hex(dacAddr)}")
        print(f"    CHANNEL: {channel}")
        print(f"    VOLTAGE: {float(voltage)}")
        print(f"10b DAC VAL: {format(val,'#06x')} {format(val,'10b')}")
        print(f"        MSB: {format(msb,'#06x')} {format(msb,'08b')}")
        print(f"        LSB: {format(lsb,'#06x')} {format(lsb,'08b')}")

    # Send 16b to a 10b DAC which expects: MSB LSB = [b9,b8,b7,b6,b5,b4,b3,b2] [b1,b0,x,x,x,x,x,x] 
    def writeToDac(self,dacAddr,channel,voltage):
        val=self.voltageToDac10bit(voltage)
        dac_val=val<<6
        msb=dac_val>>8 # most significant byte
        lsb=dac_val%256 # least significant byte 
        write_ca=0x30+channel # command and access byte
        command=f"sudo i2cset -y {self.dacAdcBus} {dacAddr} {write_ca} {msb} {lsb} i" # shell command 
        subprocess.run(command,shell=True)
        #self.printDacReadWrite(dacAddr,channel,write_ca,voltage,val,msb,lsb) # for debugging 
        time.sleep(0.01)

    def readFromDac(self,dacAddr,channel):
        read_ca=0x00+channel # command and access byte
        command=f"sudo i2cget -y {self.dacAdcBus} {dacAddr} {read_ca} i" # shell command 
        result=subprocess.run(command,shell=True,capture_output=True,text=True).stdout.strip()
        msb=int(result[0:4],16)
        lsb=int(result[5:9],16)
        val=((msb<<8)+lsb)>>6
        voltage=self.Dac10bitToVoltage(val)
        #self.printDacReadWrite(dacAddr,channel,read_ca,voltage,val,msb,lsb) # for debugging
        time.sleep(0.01)
        return voltage

    def write32bToMem(self,addr,val):
        command=f"sudo devmem {addr} 32 {val}"
        subprocess.run(command,shell=True)
        time.sleep(0.01)

    def read32bFromMem(self,addr):
        command=f"sudo devmem {addr} 32"
        result=subprocess.run(command,shell=True,capture_output=True,text=True).stdout.strip()
        return result

    def setMasks(self):
        print("------ CHANNEL MASKS ------")
        masks=self.masks.reverse()
        bstring=''.join(str(mask) for mask in self.masks)
        val=int(bstring,2)
        self.write32bToMem(self.regAddr,val)
        result=self.read32bFromMem(self.regAddr) 
        result=str(bin(int(result,16))[2:])[::-1]
        for i in range(len(self.masks)):
            if int(result[i])==1:
                print(f"CH {i+1:>2}: ON")
            else:
                print(f"CH {i+1:>2}: OFF")

    def setThresholds(self):
        print("------ COMPARATOR THRESHOLDS ------")
        for thresh in self.thresholds: # high, medium, low etc...
            self.writeToDac(self.threshDacAddr,self.threshDacRegMap[thresh],self.thresholds[thresh])
            voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap[thresh])
            print(f"{thresh:>7} set to {voltage:>1} V")

    def setWidths(self):
        print("------ COMPARATOR WIDTHS ------")
        for width in self.widths: # high, medium, low etc...
            self.writeToDac(self.widthDacAddr,self.widthDacRegMap[width],self.widths[width])
            voltage=self.readFromDac(self.widthDacAddr,self.widthDacRegMap[width])
            print(f"{width:>7} set to {voltage:>1} V")

def main():

    if len(sys.argv)!=2:
        print("This script expects one argument: the CASB's json config file")
        sys.exit(1) 

    file = sys.argv[1]  

    loader=DataLoader(file)
    loader.parse()
    loader.validate()
    #loader.print() # for debugging
    masks,thresholds,widths=loader.getData() 

    casb=CASB(masks,thresholds,widths) 
    casb.setMasks()
    casb.setThresholds()
    casb.setWidths()

    #Then make loop that restores baseline

if __name__ == "__main__":
    main()

