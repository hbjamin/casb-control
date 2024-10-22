#!/usr/bin/env python

import sys
import math
import time
import json
import subprocess
import numpy as np

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
            if int(self.masks[i])==1:
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
                 'Med':0,
             'AttnTot':1,
                'High':2,
                 'Tot':3,
                 'BLR':4,
                 'Low':5,
             'AttnBLR':6
        }
        self.widthDacRegMap={
                 'Low':0,
                 'Med':1,
                 'Tot':2,
                'High':3,
             'AttnTot':4
        }
        self.dacVref=3.19
        self.adcVref=3.187
        self.BL=0
        self.BLR=0
        self.attnBL=0
        self.attnBLR=0

    def voltageToDac10bit(self,voltage):
        bits=10
        resolution=self.dacVref/(math.pow(2,bits))
        return round(voltage/resolution)
    
    def Dac10bitToVoltage(self,val):
        bits=10
        resolution=self.dacVref/(math.pow(2,bits))
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
        result=str(format(int(result,16),'032b')[2:])[::-1]
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

    def adc16bitToVoltage(self,val):  
        # flip msb and lsb
        msb=(int(val,16)&0x00ff)<<8
        lsb=(int(val,16)&0xff00)>>8
        val=msb+lsb
        addr=(val&0x7000)>>12
        data=(val&0x0ffc)>>2
        bits=10
        voltage=self.adcVref*data/(math.pow(2,bits))
        #print(val)
        #print(format(val,'04x'),'or',format(val,'016b'))
        #print('addr',bin(addr))
        #print('data',bin(data),format(data,'010b'))
        #print('data',data)
        #print('max',math.pow(2,bits))
        return voltage

    def readFromAdc(self,channel):
        ca_byte=0x80+(channel<<4)
        command=f"sudo i2cget -y 0 0x22 {ca_byte} w"
        result=subprocess.run(command,shell=True,capture_output=True,text=True).stdout.strip()
        voltage=self.adc16bitToVoltage(result)
        #print(f"Reading from channel {channel}")
        #print(f"Voltage is {voltage}")
        time.sleep(0.001)
        return voltage

    def getBaselines(self,p=False):
        self.BL=self.readFromAdc(0)
        self.BLR=self.readFromAdc(1)
        self.attnBL=self.readFromAdc(2)
        self.attnBLR=self.readFromAdc(3)
        if p:
            print("------ GET BASELINES ------")
            print(f"     BL is {self.BL:.3f} V")
            print(f"    BLR is {self.BLR:.3f} V")
            print(f" AttnBL is {self.attnBL:.3f} V")
            print(f"AttnBLR is {self.attnBLR:.3f} V")

    def setBaselines(self,BLR,attnBLR,p=False):
        self.writeToDac(self.threshDacAddr,self.threshDacRegMap['BLR'],BLR)
        voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap['BLR'])
        self.writeToDac(self.threshDacAddr,self.threshDacRegMap['AttnBLR'],attnBLR)
        voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap['AttnBLR'])
        if p:
            print("------ SET BASELINES ------")
            print(f"UnityBL set to {voltage:>1} V")
            print(f" AttnBL set to {voltage:>1} V")
    
    def setMiddleBaselines(self):
        print("------ QUICK SCAN BASELINES ------")
        # Min baselines can set
        self.setBaselines(0,0)
        self.getBaselines()
        minBLR=self.BLR
        minAttnBLR=self.attnBLR
        # Max baselines can set
        self.setBaselines(self.adcVref,self.adcVref)
        self.getBaselines()
        maxBLR=self.BLR
        maxAttnBLR=self.attnBLR
        bestBLR=(minBLR+maxBLR)/2
        bestAttnBLR=(minAttnBLR+maxAttnBLR)/2
        print(f"Can set unity baseline between {minBLR:.3f} and {maxBLR:.3f} V")
        print(f"Can set atten baseline between {minAttnBLR:.3f} and {maxAttnBLR:.3f} V")
        self.setBaselines(bestBLR,bestAttnBLR,p=True)
        self.getBaselines(p=True)

    def scanBaselines(self):
        print("------ SCAN BASELINES ------")
        dac=np.arange(0,self.adcVref,0.05)
        adc=[]
        adc_attn=[]
        for v in dac:
            self.setBaselines(v,v)
            self.getBaselines()
            adc.append(self.BLR)
            adc_attn.append(self.attnBLR)
        print(dac)
        print(adc)
        print(adc_attn)



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
    casb.setMiddleBaselines()
    casb.scanBaselines()
    casb.setBaselines(casb.adcVref,casb.adcVref,p=True)
    #casb.getBaselines(p=True)
    casb.setThresholds()
    casb.setWidths()
    

if __name__ == "__main__":
    main()

