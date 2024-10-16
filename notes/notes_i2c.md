# Introducing i2c
- Serial communication protocol for microcontroller, ADCs, DACs, EEPROMs, I/O devices and real-time clocks
- Can communicate with multiple slave devices connected to the same bus
- Communication can only occur in one direction at a time
- Serial Data Wire (`SDA`) carries the data packets sent by the master and slave devices
- Serial Clock (`SCL`) carries a clock signal generated by the master and synchronises the data packets on the SDA wire between master and slaves
    - `SDA` and `SCL` are pulled up to `+Vdd` (+3.3V or +5V) via a resistor, so their default state is high
    - Data is sent over the i2c bus by pulling the SDA wire low to 0V
- Each slave device on the i2c bus has a unique address (usually 7-bit but can be 10-bit)
    - The master will send that address at the start of any communication, and only the slave on that address will respond
- Each byte in an i2c packet is 8 bits long, followed by a 9th awcknowledge bit generated by the receiving slave device pulling the SDA wire low for one clock cycle. Acknowledge bits are typically `ACK`. IF a slave does not acknowledge the byte, the acknowledge bit is shown as `NACK`
- 1 bit start condition
    - Master start condition: HIGH --> LOW on SDA while SCL is high
    - Master stop condition: LOW --> HIGH on SDA while SCL is high
- 7 bit address
- 1 bit read=1/write=0
- 8 bit data byte
- ACK/NACK bit
- 8 biut datay byte
- ACK/NACK bit
- stop condition

# Installing i2c tools and python libraries
- Adrian's petalinux rootfs comes with all the i2c tools needed :)
- Can set the bus speed by editing... ?
    - Look at zturn spec sheets to find the recommended speed

# i2c device addresses
- To find a list of addressed connected use
```bash
sudo i2cdetect -y 1
```

# Available commands in i2c tools
- `i2cdetect` detects i2c chips connected to the bus
    - `-y` disables interactive mode
    - `-l` shows all installed i2c buses
- `i2cdump` examine and read i2c registers on a connected device
- `i2cget` read from i2c bus chip registers on a connected device
- `i2cset` set i2c registers on a connected device with new data
- `i2ctransfer` set user-defined i2c messages in one transfer to a connected device

# Programming i2c with python

### Using Hexadecimal
- The number of bytes is the number of hex characters divided by two
    - 00 = 1 byte or 8 bits
    - 0000 = 2 bytes or 16 bits
- hex numbers have `0x` as a prefix
- binary numbers have `0b` as a prefix

# The smbus library
https://www.abelectronics.co.uk/kb/article/1094/i2c-part-4-programming-i2c-with-python 


