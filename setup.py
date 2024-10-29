#!/usr/bin/env python

import sys
import math
import time
import subprocess
import numpy as np
from json_parser import DataLoader

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
        self.baselines={
                'Unity':0,
                 'Attn':0
        }
        #self.shiftsInBLR={
        #         'Low':0,
        #         'Med':1,
        #         'Tot':2,
        #}
        self.shiftsInBLR=[0.0015,0.0003,0.0055,0.0000,0.0000] # Baseline shift going to HIGH, MED, LOW comparators
        self.dacVref=3.19
        self.adcVref=3.187
        self.BL=0
        self.BLR=0
        self.attnBL=0
        self.attnBLR=0
        self.scanBLR=[]
        self.scanAttnBLR=[]

    def voltageToDac10bit(self,voltage):
        bits=10
        resolution=self.dacVref/(math.pow(2,bits))
        return round(voltage/resolution)
    
    def Dac10bitToVoltage(self,val):
        bits=10
        resolution=self.dacVref/(math.pow(2,bits))
        return round(val*resolution,4)

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
        command=["sudo","-S","i2cset","-y",str(self.dacAdcBus),str(dacAddr),str(write_ca),str(msb),str(lsb),"i"] # shell command 
        process=subprocess.Popen(command,stdin=subprocess.PIPE,text=True)
        process.stdin.write("petalinux")
        process.stdin.flush()
        process.communicate()
        #self.printDacReadWrite(dacAddr,channel,write_ca,voltage,val,msb,lsb) # for debugging 
        time.sleep(0.01)

    def readFromDac(self,dacAddr,channel):
        read_ca=0x00+channel # command and access byte
        command=["sudo","-S","i2cget","-y",str(self.dacAdcBus),str(dacAddr),str(read_ca),"i"]
        #command=f"sudo i2cget -y {self.dacAdcBus} {dacAddr} {read_ca} i" # shell command 
        #result=subprocess.run(command,shell=True,capture_output=True,text=True).stdout.strip()
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        process.stdin.write("petalinux")
        process.stdin.flush()
        output,_=process.communicate()
        result=output.strip()
        msb=int(result[0:4],16)
        lsb=int(result[5:9],16)
        val=((msb<<8)+lsb)>>6
        voltage=self.Dac10bitToVoltage(val)
        #self.printDacReadWrite(dacAddr,channel,read_ca,voltage,val,msb,lsb) # for debugging
        time.sleep(0.01)
        return voltage

    def write32bToMem(self,addr,val):
        command=["sudo","-S","devmem",str(addr),"32",str(val)]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,text=True)
        process.stdin.write("petalinux")
        process.stdin.flush()
        process.communicate()
        time.sleep(0.01)

    def read32bFromMem(self,addr):
        command=["sudo","-S","devmem",str(addr),"32"]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        process.stdin.write("petalinux")
        process.stdin.flush()
        output,_=process.communicate()
        result=output.strip() 
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
        print(f"Should shift [thresh] up by [baseline] + [channel's constant offset]") 
        print(f"NOTE: This will not be perfect due to 10-bit DAC resolution of ~0.0033")
        i=0
        for thresh in self.thresholds: # high, medium, low etc...
            if thresh=='AttnTot':
                shifted_thresh=self.thresholds[thresh]+self.attnBLR+self.shiftsInBLR[i]
                self.writeToDac(self.threshDacAddr,self.threshDacRegMap[thresh],shifted_thresh)
                voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap[thresh])
                print(f"Should set {thresh:>7} to {self.thresholds[thresh]:.4f} + {self.attnBLR:.4f} + {self.shiftsInBLR[i]:.4f} = {shifted_thresh:.4f}... actually set to {voltage:>{1}.4f} V")
            else:
                shifted_thresh=self.thresholds[thresh]+self.BLR+self.shiftsInBLR[i]
                self.writeToDac(self.threshDacAddr,self.threshDacRegMap[thresh],shifted_thresh)
                voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap[thresh])
                print(f"Should set {thresh:>7} to {self.thresholds[thresh]:.4f} + {self.BLR:.4f} + {self.shiftsInBLR[i]:.4f} = {shifted_thresh:.4f}... actually set to {voltage:>{1}.4f} V")
            i+=1

    def setWidths(self):
        print("------ COMPARATOR WIDTHS ------")
        for width in self.widths: # high, medium, low etc...
            self.writeToDac(self.widthDacAddr,self.widthDacRegMap[width],self.widths[width])
            voltage=self.readFromDac(self.widthDacAddr,self.widthDacRegMap[width])
            print(f"Should set {width:>7} to {self.widths[width]:.4f} actually set to {voltage:>{1}.4f}")

    def adc16bitToVoltage(self,val,p=False):  
        # flip msb and lsb (for some reason this is necessary)
        msb=(int(val,16)&0x00ff)<<8
        lsb=(int(val,16)&0xff00)>>8
        val=msb+lsb
        addr=(val&0x7000)>>12
        data=(val&0x0ffc)>>2
        bits=10
        voltage=self.adcVref*data/(math.pow(2,bits))
        if p==True:
            print(val)
            print(format(val,'04x'),'or',format(val,'016b'))
            print('addr',bin(addr))
            print('data',bin(data),format(data,'010b'))
            print('data',data)
            print('max',math.pow(2,bits))
        return voltage

    def readFromAdc(self,channel,p=False):
        ca_byte=0x80+(channel<<4)
        command=["sudo","-S","i2cget","-y","0","0x22",str(ca_byte),"w"]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        process.stdin.write("petalinux")
        process.stdin.flush()
        output,_=process.communicate()
        result=output.strip() 
        #command=f"sudo i2cget -y 0 0x22 {ca_byte} w"
        #result=subprocess.run(command,shell=True,capture_output=True,text=True).stdout.strip()
        voltage=self.adc16bitToVoltage(result)
        time.sleep(0.001)
        if p==True:
            print(f"Reading from channel {channel}")
            print(f"Voltage is {voltage}")
        return voltage

    def getBaselines(self,p=False):
        self.BL=self.readFromAdc(0)
        self.BLR=self.readFromAdc(1)
        self.attnBL=self.readFromAdc(2)
        self.attnBLR=self.readFromAdc(3)
        if p==True:
            print("------ GET BASELINES ------")
            print(f"Unity baseline is {self.BLR:.4f} V")
            print(f" Attn baseline is {self.attnBLR:.4f} V")

    # Takes in DAC value used to set a baseline 
    def setBaselineDAC(self,BLR,attnBLR,p=False):
        self.writeToDac(self.threshDacAddr,self.threshDacRegMap['BLR'],BLR)
        voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap['BLR'])
        self.writeToDac(self.threshDacAddr,self.threshDacRegMap['AttnBLR'],attnBLR)
        voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap['AttnBLR'])
        if p:
            print("------ SET BASELINES ------")
            print(f"UnityBL set to {voltage:>1} V")
            print(f" AttnBL set to {voltage:>1} V")

    # Takes in the baseline you want to measure with the ADC
    # Uses result from self.scanBaselines() to do this conversion 
    def setBaselineADC(self,p=False):
        BLR=self.baselines['Unity']
        attnBLR=self.baselines['Attn']
        # Make sure the desired baselines are within the possible ranges
        if BLR<self.scanBLR[0] or BLR>self.scanBLR[-1]:
            print(f"ERROR! Cannot set unity baseline to {BLR:.4f}. Must be between {self.scanBLR[0]:.4f} and {self.scanBLR[-1]:.4f}")
            return 0
        if attnBLR<self.scanAttnBLR[0] or attnBLR>self.scanAttnBLR[-1]:
            print(f"ERROR   Cannot set attn baseline to {attnBLR:.4f}. Must be between {self.scanAttnBLR[0]:.4f} and {self.scanAttnBLR[-1]:.4f}")
            return 0
        # Figure out the corresponding DAC value to program
        dac=np.arange(0,self.adcVref,0.1)
        for i in range(len(dac)):
            if BLR<self.scanBLR[i]:
                BLR=dac[i-1]
                break
        for i in range(len(dac)):
            if attnBLR<self.scanAttnBLR[i]:
                attnBLR=dac[i-1]
                break
        self.writeToDac(self.threshDacAddr,self.threshDacRegMap['BLR'],BLR)
        voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap['BLR'])
        self.writeToDac(self.threshDacAddr,self.threshDacRegMap['AttnBLR'],attnBLR)
        voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegMap['AttnBLR'])
        if p:
            print("------ SET BASELINES ------")
            print(f"UnityBL set to {voltage:>1} V")
            print(f" AttnBL set to {voltage:>1} V")

    def quickScanBaselines(self):
        print("------ QUICK BASELINE SCAN ------")
        # Min baselines 
        self.setBaselineDAC(0,0)
        self.getBaselines()
        minBLR=self.BLR
        minAttnBLR=self.attnBLR
        # Max baselines
        self.setBaselineDAC(self.adcVref,self.adcVref)
        self.getBaselines()
        maxBLR=self.BLR
        maxAttnBLR=self.attnBLR
        print(f"Unity baseline can be set from {minBLR:.4f} to {maxBLR:.4f} V")
        print(f" Attn baseline can be set from {minAttnBLR:.4f} to {maxAttnBLR:.4f} V")

    def scanBaselines(self):
        print("------ BASELINE SCAN ------")
        dac=np.arange(0,self.adcVref,0.1)
        adc=[]
        adc_attn=[]
        for v in dac:
            self.setBaselineDAC(v,v)
            self.getBaselines()
            adc.append(self.BLR)
            adc_attn.append(self.attnBLR)
        self.scanBLR=adc
        self.scanAttnBLR=adc_attn
        mid_adc=0
        mid_adc_attn=0
        for i in range(len(adc)):
            if adc[i]>((adc[0]+adc[-1])/2): 
                mid_adc=adc[i-1]
                break
        for i in range(len(adc)):
            if adc_attn[i]>((adc_attn[0]+adc_attn[-1])/2): 
                mid_adc_attn=adc_attn[i-1]
                break
        self.baselines['Unity']=mid_adc
        self.baselines['Attn']=mid_adc_attn
        print(f"Unity baseline can be set between {adc[0]:>{3}.4f} and {adc[-1]:.4f} V")
        print(f"            Setting to median value of {self.baselines['Unity']:.4f} V")
        print(f" Attn baseline can be set between {adc_attn[0]:>{3}.4f} and {adc_attn[-1]:.4f} V")
        print(f"            Setting to median value of {self.baselines['Attn']:.4f} V")


def main():

    if len(sys.argv)!=2:
        print("This script expects one argument: the CASB's json config file")
        sys.exit(1) 

    file = sys.argv[1]  

    loader=DataLoader(file)
    loader.parse()
    if loader.validate()==False:
        return 0
    #loader.print() # for debugging
    masks,thresholds,widths=loader.getData() 
    
    casb=CASB(masks,thresholds,widths) 
    casb.setMasks()
    #casb.quickScanBaselines()
    casb.scanBaselines()
    casb.setBaselineADC()
    casb.getBaselines(p=True)
    casb.setThresholds()
    casb.setWidths()
    

if __name__ == "__main__":
    main()

