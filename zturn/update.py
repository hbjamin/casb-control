#!/usr/bin/env python

import sys
import math
import time
import subprocess
import numpy as np
import argparse

# GLOBAL VARIABLES??
### Baseline tolerance?
### Vref?

class CASB():
    def __init__(self):   


        # for i2c communication
        self.i2cBus=0 # bus number
        self.threshDacAddr=0x48 # address of DAC for setting thresholds of comparators
        self.widthDacAddr=0x49 # address of DAC for setting output widths of comparators
        self.adcAddr=0x22 # address of ADC for reading baselines
        self.regAddr=0x43C0000C # address of register block in Vivado for setting channel masks
        self.boardIdAddr=0x50 # ----- unused -----

        # dictionaries for accessing registers
        self.threshDacRegDict={ # comparator name --> register of threshold DAC
                   'h':2,
                   'm':0,  
                   'l':5,  
                   't':3, 
                   'a':1,
            'UnityBLR':4, # for restoring unity path baseline  
             'AttnBLR':6  # for restoring attenuated path baseline
        }
        self.minThresh={
                   'h':0.02,
                   'm':0.017,  
                   'l':0.017,  
                   't':0.0000, 
                   'a':0.0000
        }
        self.widthDacRegDict={ # comparator name --> register of width DAC
                 'h':3,
                 'm':1,
                 'l':0,
                 't':2, # ----- unused?? -----
                 'a':4 # ----- unused?? -----
        }
        self.baselineAdcRegDict={ # baseline name --> register of ADC
            'UnityBL':0,
           'UnityBLR':1,
             'AttnBL':2,
            'AttnBLR':3,
       'HighUnityBLR':5, 
        'MedUnityBLR':4, 
        'LowUnityBLR':7  
        }
       
        # for baseine restoration 
        self.scannedBaselines={ # for finding optimal baseline
           'UnityBLR':[],
            'AttnBLR':[],
        }
        self.optimalBaselines={ # what to restore baseline to
           'UnityBLR':0,
            'AttnBLR':0,
        }
        self.currentBaselines={ 
            'UnityBL':0, # pre-restoration 
           'UnityBLR':0,
             'AttnBL':0, # pre-restoration
            'AttnBLR':0,
       'HighUnityBLR':0, # result of post-restoration shift 
        'MedUnityBLR':0, # result of post-restoration shift 
        'LowUnityBLR':0  # result of post-restoration shift 
        }

        # ----- COULD USE LAST ADC REGISTER HERE ----- short them together so only have to measure one? and have same resolution??
        # reference voltages for DAC and ADC 
        self.dacVref=3.19 # measured with DVM ----- redo? -----
        self.adcVref=3.187 # measured with DVM ----- stable? -----

    def voltageToDac(self,voltage):
        bits=12
        resolution=self.dacVref/(math.pow(2,bits))
        return round(voltage/resolution) 
    
    def DacToVoltage(self,val):
        bits=12
        resolution=self.dacVref/(math.pow(2,bits))
        return round(val*resolution,4)

    def printDacReadWrite(self,dacAddr,channel,ca,voltage,val,msb,lsb):
        if int(format(ca,'#04x')[2])==3:
            print(f"Writing ------------") 
        else:
            print(f"Reading ------------") 
        print(f"    I2C BUS: {self.i2cBus}")
        print(f"DAC ADDRESS: {hex(dacAddr)}")
        print(f"    CHANNEL: {channel}")
        print(f"    VOLTAGE: {float(voltage)}")
        print(f"12b DAC VAL: {format(val,'#06x')} {format(val,'12b')}")
        print(f"        MSB: {format(msb,'#06x')} {format(msb,'08b')}")
        print(f"        LSB: {format(lsb,'#06x')} {format(lsb,'08b')}")

    # DAC expects: MSB, LSB = [b11,b10,b9,b8,b7,b6,b5,b4], [b3,b2,b1,b0,x,x,x,x] 
    def writeToDac(self,dacAddr,channel,voltage,p=False):
        val=self.voltageToDac(voltage)
        dac_val=val<<4 # 4 lsb not used
        msb=dac_val>>8 
        lsb=dac_val%256 
        write_ca=0x30+channel # write command and access byte
        command=["sudo","-S","i2cset","-y",str(self.i2cBus),str(dacAddr),str(write_ca),str(msb),str(lsb),"i"] # shell command with superuser privileges
        process=subprocess.Popen(command,stdin=subprocess.PIPE,text=True) # stdin set to PIP for password input
        process.stdin.write("petalinux\n") # password
        process.stdin.flush() # ensure password is sent immediately
        process.communicate() # handle output steams
        if p==True: 
            self.printDacReadWrite(dacAddr,channel,write_ca,voltage,val,msb,lsb)  
        time.sleep(0.01)

    def readFromDac(self,dacAddr,channel,p=False):
        read_ca=0x00+channel # read command and access byte 
        command=["sudo","-S","i2cget","-y",str(self.i2cBus),str(dacAddr),str(read_ca),"i"]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True) 
        process.stdin.write("petalinux\n") 
        process.stdin.flush()
        output,_=process.communicate()
        result=output.strip()
        msb=int(result[0:4],16)
        lsb=int(result[5:9],16)
        val=((msb<<8)+lsb)>>4 # 4 lsb not used
        voltage=self.DacToVoltage(val)
        time.sleep(0.01)
        if p==True: 
            self.printDacReadWrite(dacAddr,channel,read_ca,voltage,val,msb,lsb) 
        return voltage

    def writeToMem(self,addr,val,nbits):
        command=["sudo","-S","devmem",str(addr),str(nbits),str(val)]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,text=True)
        process.stdin.write("petalinux\n")
        process.stdin.flush()
        process.communicate()
        time.sleep(0.01)

    def readFromMem(self,addr,nbits):
        command=["sudo","-S","devmem",str(addr),str(nbits)]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        process.stdin.write("petalinux\n")
        process.stdin.flush()
        output,_=process.communicate()
        result=output.strip() 
        return result

    def updateChannelMask(self,channel,mask):
        print("-------------------------------")
        print(f"Updating channel {channel} mask to {mask}") 
        current=int(self.readFromMem(self.regAddr,32),16)
        bmask=1<<(channel-1) # create bit mask for channel number (starting from 1)
        current &= ~bmask # clear the nth bit
        if mask==1:
            current|=bmask
        current=int(bin(current),2)
        self.writeToMem(self.regAddr,current,32)
        result=self.readFromMem(self.regAddr,32) 
        result=str(format(int(result,16),'032b')[2:])[::-1]
        print("-------------------------------")
        print("------ SET CHANNEL MASKS ------")
        print("-------------------------------")
        for i in range(20):
            if int(result[i])==1:
                print(f"CH {i+1:>2}: ON")
            else:
                print(f"CH {i+1:>2}: OFF")
        

    def setThresholds(self,p=False):
        if p:
            print("---------------------------------------")
            print("------ SET COMPARATOR THRESHOLDS ------")
            print("---------------------------------------")
            print(f"[threshold] + [measured baseline] = [shifted threshold] (measured threshold)")
        i=0
        for thresh in self.thresholds: # high, medium, low etc...
            baseline=0 
            if thresh=='High':
                baseline=self.currentBaselines['HighUnityBLR']
            elif thresh=='Med':
                baseline=self.currentBaselines['MedUnityBLR']
            elif thresh=='Low':
                baseline=self.currentBaselines['LowUnityBLR']
            elif thresh=='Tot':
                baseline=self.currentBaselines['UnityBLR'] # technically wrong
            elif thresh=='AttnTot':
                baseline=self.currentBaselines['AttnBLR'] # probably wrong?
            shifted_thresh=self.thresholds[thresh]+baseline
            self.writeToDac(self.threshDacAddr,self.threshDacRegDict[thresh],shifted_thresh)
            voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegDict[thresh])
            if p:
                print(f"Setting {thresh:>7} to {self.thresholds[thresh]:.4f} + {baseline:.4f} = {shifted_thresh:.4f} ({voltage:>{1}.4f}) Volts")

        
    def updateComparatorThreshold(self,comp,threshold):
        print("---------------------------------------")
        print(f"Updating {comp} comparator threshold to {threshold}")
        print("---------------------------------------")
        print("------ SET COMPARATOR THRESHOLDS ------")
        print("---------------------------------------")
        print("ADC & DAC resolution is 0.00078 Volts")
        print("---------------------------------------")
        print(f"[threshold] + [measured baseline] - [min threshold 100% PTB trigger]  = (measured threshold)")
        print("---------------------------------------")
        i=0
        baseline=0 
        comparators=['h','m','l','t','a']
        self.measureBaselines()
        for comparator in comparators:
            if comparator=='h':
                baseline=self.currentBaselines['HighUnityBLR']
            elif comparator=='m':
                baseline=self.currentBaselines['MedUnityBLR']
            elif comparator=='l':
                baseline=self.currentBaselines['LowUnityBLR']
            elif comparator=='t':
                baseline=self.currentBaselines['UnityBLR'] # technically wrong
            elif comparator=='a':
                baseline=self.currentBaselines['AttnBLR'] # probably wrong?
            if comparator==comp:
                shifted_thresh=threshold+baseline-self.minThresh[comparator]
                self.writeToDac(self.threshDacAddr,self.threshDacRegDict[comparator],shifted_thresh)
                voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegDict[comparator])
                print(f"Setting   {comparator} threshold        to {threshold:.4f} + {baseline:.4f} - {self.minThresh[comparator]:.4f} = {voltage:>{1}.4f} Volts")
            else:
                voltage=self.readFromDac(self.threshDacAddr,self.threshDacRegDict[comparator])
                thresh=voltage-baseline+self.minThresh[comparator]
                print(f"Currently {comparator} threshold is set to {thresh:.4f} + {baseline:.4f} - {self.minThresh[comparator]:.4f} = {voltage:>{1}.4f} Volts")

    def updateComparatorWidth(self,comp,width):
        print("---------------------------------------")
        print(f"Updating {comp} comparator width to {width}")
        print("---------------------------------------")
        print("------ SET COMPARATOR WIDTHS ------")
        print("---------------------------------------")
        print("ADC & DAC resolution is 0.00078 Volts")
        print("---------------------------------------")
        print(f"[width] = (measured width)")
        print("---------------------------------------")
        i=0
        comparators=['h','m','l','t','a']
        for comparator in comparators:
            if comparator==comp:
                self.writeToDac(self.widthDacAddr,self.widthDacRegDict[comparator],width)
                voltage=self.readFromDac(self.widthDacAddr,self.widthDacRegDict[comparator])
                print(f"Setting   {comparator} width        to {width:.4f} = {voltage:>{1}.4f} Volts")
            else:
                voltage=self.readFromDac(self.widthDacAddr,self.widthDacRegDict[comparator])
                print(f"Currently {comparator} width is set to {width:.4f} = {voltage:>{1}.4f} Volts")
    
    def setWidths(self,p=False):
        if p:
            print("-----------------------------------")
            print("------ SET COMPARATOR WIDTHS ------")
            print("-----------------------------------")
            print(f"[width] (measured width)")
        for width in self.widths: # high, medium, low etc...
            self.writeToDac(self.widthDacAddr,self.widthDacRegDict[width],self.widths[width])
            voltage=self.readFromDac(self.widthDacAddr,self.widthDacRegDict[width])
            if p:
                print(f"Setting {width:>7} to {self.widths[width]:.4f} ({voltage:>{1}.4f}) Volts")

    def adcToVoltage(self,val,p=False):  
        # flip msb and lsb (they are sent back flipped?)
        msb=(int(val,16)&0x00ff)<<8
        lsb=(int(val,16)&0xff00)>>8
        val=msb+lsb
        addr=(val&0x7000)>>12
        data=(val&0xfff) 
        bits=12
        voltage=self.adcVref*data/(math.pow(2,bits))
        if p:
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
        process.stdin.write("petalinux\n")
        process.stdin.flush()
        output,_=process.communicate()
        result=output.strip() 
        voltage=self.adcToVoltage(result)
        time.sleep(0.001)
        if p:
            print(f"Reading from channel {channel}")
            print(f"Voltage is {voltage}")
        return voltage

    def measureBaselines(self,p=False):
        if p:
            print("---------------------------")
            print("------ GET BASELINES ------")
            print("---------------------------")
        self.currentBaselines['UnityBL']=self.readFromAdc(self.baselineAdcRegDict['UnityBL'])
        self.currentBaselines['UnityBLR']=self.readFromAdc(self.baselineAdcRegDict['UnityBLR'])
        self.currentBaselines['AttnBL']=self.readFromAdc(self.baselineAdcRegDict['AttnBL'])
        self.currentBaselines['AttnBLR']=self.readFromAdc(self.baselineAdcRegDict['AttnBLR'])
        self.currentBaselines['HighUnityBLR']=self.readFromAdc(self.baselineAdcRegDict['HighUnityBLR'])
        self.currentBaselines['MedUnityBLR']=self.readFromAdc(self.baselineAdcRegDict['MedUnityBLR'])
        self.currentBaselines['LowUnityBLR']=self.readFromAdc(self.baselineAdcRegDict['LowUnityBLR'])
        if p:
            print(f" Restored unity baseline is {self.currentBaselines['UnityBLR']:.4f} Volts")
            print(f"High comparator baseline is {self.currentBaselines['HighUnityBLR']:.4f} Volts")
            print(f" Med comparator baseline is {self.currentBaselines['MedUnityBLR']:.4f} Volts")
            print(f" Low comparator baseline is {self.currentBaselines['LowUnityBLR']:.4f} Volts")
            print(f"  Restored attn baseline is {self.currentBaselines['AttnBLR']:.4f} Volts")

    # Takes in DAC value used to set a baseline 
    def setBaselines(self,unity,attn,p=False):
        self.writeToDac(self.threshDacAddr,self.threshDacRegDict['UnityBLR'],unity)
        unity_baseline=self.readFromDac(self.threshDacAddr,self.threshDacRegDict['UnityBLR'])
        self.writeToDac(self.threshDacAddr,self.threshDacRegDict['AttnBLR'],attn)
        attn_baseline=self.readFromDac(self.threshDacAddr,self.threshDacRegDict['AttnBLR'])
        if p:
            print(f"Unity baseline restored to {unity_baseline:>1} Volts")
            print(f" Attn baseline restored to {attn_baseline:>1} Volts")

    # Uses result from self.scanBaselines()  
    def setOptimalBaselines(self,p=False):
        if p:
            print("-----------------------------")
            print("------- SET BASELINES ------")
            print("-----------------------------")
        unity=self.optimalBaselines['UnityBLR']
        attn=self.optimalBaselines['AttnBLR']
        # Make sure the optimal baselines are within the possible ranges
        if unity<self.scannedBaselines['UnityBLR'][0] or unity>self.scannedBaselines['UnityBLR'][-1]:
            print(f"ERROR! Cannot set unity baseline to {unity:.4f}. Must be between {self.scannedBaselines['UnityBLR'][0]:.4f} and {self.scannedBaselines['Unity'][-1]:.4f} Volts")
            return 0
        if attn<self.scannedBaselines['AttnBLR'][0] or attn>self.scannedBaselines['AttnBLR'][-1]:
            print(f"ERROR! Cannot set attn baseline to {attn:.4f}. Must be between {self.scannedBaselines['AttnBLR'][0]:.4f} and {self.scannedBaselines['AttnBLR'][-1]:.4f} Volts")
            return 0
        # Figure out the corresponding DAC value to program
        dac=np.arange(0,self.adcVref,0.05)
        for i in range(len(dac)):
            if unity<self.scannedBaselines['UnityBLR'][i]:
                unity=dac[i-1]
                break
        for i in range(len(dac)):
            if attn<self.scannedBaselines['AttnBLR'][i]:
                attn=dac[i-1]
                break
        self.setBaselines(unity,attn)
        self.measureBaselines()
        self.optimalBaselines['UnityBLR']=self.currentBaselines['UnityBLR'] # correct optimal baseline due to ADC resolution
        self.optimalBaselines['AttnBLR']=self.currentBaselines['AttnBLR'] # correct optimal baseline due to ADC resolution
        if p:
            print(f"Set unity baseline to optimal value of {self.optimalBaselines['UnityBLR']:.4f} Volts")
            print(f"Set unity baseline to optimal value of {self.optimalBaselines['AttnBLR']:.4f} Volts")


    def quickScanBaselines(self,p=False):
        if p:
            print("---------------------------------")
            print("------ QUICK BASELINE SCAN ------")
            print("---------------------------------")
        # Min baselines 
        self.setBaselines(0,0)
        self.measureBaselines()
        min_unity=self.currentBaselines['UnityBLR']
        min_attn=self.currentBaselines['AttnBLR']
        # Max baselines
        self.setBaselines(self.adcVref,self.adcVref)
        self.measureBaselines()
        max_unity=self.currentBaselines['UnityBLR']
        max_attn=self.currentBaselines['AttnBLR']
        if p:
            print(f"Unity baseline can be set between {min_unity:.4f} and {max_unity:.4f} Volts")
            print(f" Attn baseline can be set between {min_attn:.4f} and {max_attn:.4f} Volts")

    def scanBaselines(self,p=False):
        if p:
            print("-----------------------------")
            print("------- SCAN BASELINES ------")
            print("-----------------------------")
        # voltage domain to scan baseline over
        dac=np.arange(0,self.adcVref,0.05)
        # clear previous results
        for baseline in self.scannedBaselines:
            self.scannedBaselines[baseline]=[]
        # perform scan
        for v in dac:
            self.setBaselines(v,v)
            self.measureBaselines()
            for baseline in self.scannedBaselines:
                self.scannedBaselines[baseline].append(self.currentBaselines[baseline])
        # find optimal baselines
        for baseline in self.scannedBaselines:
            self.optimalBaselines[baseline]=(self.scannedBaselines[baseline][0]+self.scannedBaselines[baseline][-1])/2
        if p:
            print(f"Unity baseline can be set between {self.scannedBaselines['UnityBLR'][0]:.4f} and {self.scannedBaselines['UnityBLR'][-1]:.4f} Volts")
            print(f"Attn baseline can be set between {self.scannedBaselines['AttnBLR'][0]:.4f} and {self.scannedBaselines['AttnBLR'][-1]:.4f} Volts")

    def monitorBaselines(self):
        tolerance=0.005
        self.measureBaselines(p=False)
        measured=self.currentBaselines['UnityBLR']
        optimal=self.optimalBaselines['UnityBLR']
        diff=measured-optimal
        print(f"Time: {time.time()} --- Restored Unity Baseline --- Measured: {measured:.4f} --- Optimal: {optimal:.4f} --- Diff: {diff:.4f}")
        if diff>tolerance:
            print(f"CAUTION! Unity baseline drifted up by {diff:.4f}!")
        if diff<-1*tolerance:
            print(f"CAUTION! Unity baseline drifted down by {diff:.4f}!")
        # correct baseline....?
        measured=self.currentBaselines['AttnBLR']
        optimal=self.optimalBaselines['AttnBLR']
        diff=measured-optimal
        print(f"Time: {time.time()} --- Restored Attn Baseline --- Measured: {measured:.4f} --- Optimal: {optimal:.4f} --- Diff: {diff:.4f}")
        if diff>tolerance:
            print(f"CAUTION! Attn baseline drifted up by {diff:.4f}!")
        if diff<-1*tolerance:
            print(f"CAUTION! Attn baseline drifted down by {diff:.4f}!")
        

def main():

    # Parse arguments 
    parser=argparse.ArgumentParser()
    parser.add_argument('--channel','-c',type=int,default=None,help="select channel mask to update")
    parser.add_argument('--mask','-m',type=int,default=None,help="update mask")
    parser.add_argument('--comparator','-p',type=str,default=None,help="select which comparator to update") 
    parser.add_argument('--threshold','-t',type=float,default=None,help="update comparator threshold")
    parser.add_argument('--width','-w',type=float,default=None,help="update comparator width")
    args=parser.parse_args()
    
    casb=CASB()

    # Update channel mask
    if args.channel!=None and args.mask!=None:
        if args.channel>0 and args.channel<21:
            if args.mask==0 or args.mask==1:
                casb.updateChannelMask(args.channel,args.mask)
            else:
                print("Please enter 1 for ON and 0 for OFF") 
        else:
            print("Please enter a channel between 1 and 20")

    # Update comparator threshold or width
    if args.comparator!=None:
        if args.comparator=="h" or args.comparator=="m" or args.comparator=="l" or args.comparator=="t" or args.comparator =="a":
            if args.threshold!=None:
                if args.threshold>=0 and args.threshold<casb.dacVref:
                    casb.updateComparatorThreshold(args.comparator,args.threshold)
            elif args.width!=None:
                if args.width>=0 and args.width<casb.dacVref:
                    casb.updateComparatorWidth(args.comparator,args.width)
            else:
                print(f"Please enter a voltage between 0 and {casb.dacVref} Volts instead of {args.threshold}")
        else:
            print(f"Please enter a valid comparator instead of {args.comparator}")
            print("     h == High threshold")
            print("     m == Medium threshold")
            print("     l == Low threshold")
            print("     t == Time over threshold")
            print("     a == Attenuated time over threshold")


if __name__ == "__main__":
    main()

