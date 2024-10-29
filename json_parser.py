import json

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
        # Define truths 
        dac_range = (0, 3.1)
        valid_masks = {0, 1}
        comparators = {"High", "Med", "Low", "Tot", "AttnTot"} 
        # Validate channel masks
        if len(self.masks) != 20 or not all(mask in valid_masks for mask in self.masks):
            print("ERROR! Channel masks must contain 20 values of either 0 or 1")
            return False
        # Validate comparator thresholds
        if set(self.thresholds.keys()) != comparators:
            print(f"ERROR! Thresholds must include {comparators}")
            return False 
        if not all(dac_range[0] <= value <= dac_range[1] for value in self.thresholds.values()):
            print(f"ERROR! Threshold values must be within {dac_range}")
            return False
        # Validate comparator widths
        if set(self.widths.keys()) != comparators:
            print(f"ERROR! Widths must include {comparators}")
            return False, 
        if not all(dac_range[0] <= value <= dac_range[1] for value in self.widths.values()):
            print(f"ERROR! Width values must be within {dac_range}")
            return False, 
        return True

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
