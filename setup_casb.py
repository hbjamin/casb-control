#!/usr/bin/env python

from smbus import SMBus
import time
import json
import sys

def main():

    if len(sys.argv)!=2:
        print("This script expects one argument: the CASB's json config file")
        sys.exit(1)
    
    file = sys.argv[1] 
   
    with open(file, 'r') as f:
        data = json.load(f)

    THRESH_DAC_ADDRESS=0x4A
    WIDTH_DAC_ADDRESS=0x4B

    print("Channel Masks:")
    for i in range(len(data['channel_masks'])):
        if data['channel_masks'][i]==0:
            print("CH",str(i+1)+": OFF"),
        elif data['channel_masks'][i]==1:
            print("CH",str(i+1)+": ON"),
        else:
            print("CH",str(i)+": ERROR: value must be 0 or 1")
    print("\nHigh Comparator:")
    print("Threshold:", data['high_comparator']['threshold'])
    print("Width:", data['high_comparator']['width'])
    print("\nMedium Comparator:")
    print("Threshold:", data['med_comparator']['threshold'])
    print("Width:", data['med_comparator']['width'])
    print("\nLow Comparator:")
    print("Threshold:", data['low_comparator']['threshold'])
    print("Width:", data['low_comparator']['width'])
    print("\nToT Comparator:")
    print("Threshold:", data['tot_comparator']['threshold'])
    print("Width:", data['tot_comparator']['width'])
    print("\nAttenuated ToT Comparator:")
    print("Threshold:", data['attn_tot_comparator']['threshold'])
    print("Width:", data['attn_tot_comparator']['width'])


if __name__ == "__main__":
    main()


