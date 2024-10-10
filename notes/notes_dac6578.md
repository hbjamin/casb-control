# DAC6578

- This chip is a 10-bit, octal-channel, ultra-low glitch digital-to-analog converter
- It is a 2-wire serial interface that is i2c compatable 
- Operates at clock rates up to 3.4 MHz
    - Standard mode at 100 kHz
    - Fast mode at 400 kHz
    - Fast mode plus at 1 MHz
    - High-speed mode at 3.4 MHz
- Standard and fast mode have the same data transfer protocol, but high-speed mode is different
- The master generates start and stop conditions on the bus to indicate data transfer with the slaves
- The master performed device addressing for the slaves
- This chip is slave receiver and transmitter
- This chip supports 7 bit addressing  

# Standard and fast mode data transfer protocol

- Master generates start condition
- Master generates SCL pulses and then transmits on the SDA line
    - 7 bit address
    - read=1/write=0 direction bit
- The receiver must acknowledge the data 
    - The 9 bit sequences of 8 data bits and 1 acknowledge bit continues
- Master generates stop condition

# i2c update sequence

For a single update there needs to be:
    - Start condition
    - address byte (7 addr + 1 r/w)
    - command and access byte (4 c + 4 a) 
    - two data bytes 
        - Most significant data byte
        - Least significant data byte

### Address Byte

- First byte received after the start condition
- The four most significant bits of the addres are factory preset to 1001
- The next three bits are controlled by pins: can use resistors to set them high or low (or float?) so 8 combinations total

### Command and Access Byte

- Controls which command is being executed and which register is being accessed when writing or reading. 
- 00010111 is read/update dac register channel 8 

### Most and least significant data byte

- contain the data you want to pass
- have 10 bit voltage resolution, so need 2 bytes

# Questions

### How to send a start command?

- It is done automatically when you begin an i2c transaction, just like the acknowledgements and stop conditions.
