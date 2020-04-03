# Driver for the Texas Instruments HDC1080 temperature and humidity sensor
# Communication is done over I2C

from micropython import const
from machine import I2C
from time import sleep_ms

#I2C Address
HDC1080_ADDR = const(0x40)

# device register values that can be written to (do not write to others)
# used to specify location (pointer) to read from/write to
TEMP_REG = const(0x00)  # temperature register
HUMI_REG = const(0x01)  # humidity register
CONF_REG = const(0x02)  # configuration register
FSER_REG = const(0xFB)  # first two bytes of serial ID register
MSER_REG = const(0xFC)  # middle two bytes of serial ID register
LSER_REG = const(0xFD)  # last two bytes of serial ID register
MFID_REG = const(0xFE)  # manufacturer ID register
DVID_REG = const(0xFF)  # device ID register

#Configuration Register Bits
RESET_BIT =         const(0x8000)
HEATER_ENABLE =     const(0x2000)
ACQUISITION_MODE =  const(0x1000)
TEMP_RES_14BIT =    const(0x0000)
TEMP_RES_11BIT =    const(0x0400)
HUM_RES_14BIT =     const(0x0000)
HUM_RES_11BIT =     const(0x0100)
HUM_RES_8BIT =      const(0x0200)
# Delays\
STARTUP_DELAY =     const(15) #ms
MEAS_DELAY =        const(15) #ms


class HDC1080:
    def __init__(self, i2c, slave_addr=HDC1080_ADDR ):
        """Initialize a HDC1080 temperature and humidity sensor.
        Keyword arguments:
        i2c -- The i2c object (driver) used to interact through device addresses.
        slave_addr -- The slave address of the sensor (default 64 or 0x40).
        """
        self.TEMP_14BIT = TEMP_RES_14BIT
        self.TEMP_11BIT = TEMP_RES_11BIT
        self.HUM_14BIT = HUM_RES_14BIT
        self.HUM_11BIT = HUM_RES_11BIT
        self.HUM_8BIT = HUM_RES_8BIT

        self.i2c = i2c
        assert slave_addr in self.i2c.scan(), "Did not find slave %d in scan" % slave_addr
        self.addr = slave_addr
        # received data from temperature and humidity registers is two unsigned characters
        #self.fmt = '>2B'
        # Sleep for 15 ms to allow the temperature and humidity temperatures to start recording
        # Only serial number registers 0xFB and 0xFF are available at first
        sleep_ms(STARTUP_DELAY)
        # set up for 14 bit resolution (in config register) for both temperature and humidity readings
        # independent measurements for now
        data = bytearray(3)
        data[0] = CONF_REG
        data[1] = 1 << 4
        i2c.writeto(self.addr, data)

    def read_temperature(self):
        # write to the pointer register, changing it to the temperature register
        self.i2c.writeto(self.addr, bytearray([TEMP_REG]))
        sleep_ms(MEAS_DELAY)
        # per the spec, the conversion to celsius is (value / (2 ** 16)) * 165 - 40
        return ((int.from_bytes(self.i2c.readfrom(self.addr, 2), "big")) * 165 / 65536 - 40)

    def read_humidity(self):
        # write to the pointer register, changing it to the humidity register
        self.i2c.writeto(self.addr, bytearray([HUMI_REG]))
        sleep_ms(MEAS_DELAY)
        return ((int.from_bytes(self.i2c.readfrom(self.addr, 2), "big")) / 65536 * 100) # conversion per the spec

    def read_configuration_register(self):
        self.i2c.writeto(self.addr, bytearray([CONF_REG]))
        sleep_ms(MEAS_DELAY)
        return (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))

    def turnHeaterOn(self):
        config_data = bytearray(3)
        config_data[0] = CONF_REG
        config_data[1] = self.read_configuration_register()
        config_data[1] = config_data | HEATER_ENABLE 
        i2c.writeto(self.addr, config_data)
        return

    def turnHeaterOff(self):
        config_data = bytearray(3)
        config_data[0] = CONF_REG
        config_data[1] = self.read_configuration_register()
        config_data[1] = (config_data & ~HEATER_ENABLE) >> 8
        i2c.writeto(self.addr, config_data)
        return

    def setHumidityResolution(self,resolution):
        config_data = bytearray(3)
        config_data[0] = CONF_REG
        config_data[1] = self.read_configuration_register()
        config_data[1] = ((config_data & ~(UM_RES_11BIT | HUM_RES_14BIT | HUM_RES_8BIT)) | resolution) >> 8 
        i2c.writeto(self.addr, config_data)
        return

    def setTemperatureResolution(self,resolution):
        config_data = bytearray(3)
        config_data[0] = CONF_REG
        config_data[1] = self.read_configuration_register()
        config_data[1] = ((config_data & ~(TEMP_RES_11BIT | TEMP_RES_14BIT)) | resolution) >> 8 
        i2c.writeto(self.addr, config_data)
        return

    def readManufacturerID(self):
        self.i2c.writeto(self.addr, bytearray([MFID_REG]))
        sleep_ms(MEAS_DELAY)              # From the data sheet
        return (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))

    def readDeviceID(self):
        self.i2c.writeto(self.addr, bytearray([DVID_REG]))
        sleep_ms(MEAS_DELAY)              # From the data sheet
        return (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))

    def readSerialNumber(self):
        self.i2c.writeto(self.addr, bytearray([FSER_REG]))
        sleep_ms(MEAS_DELAY)             # From the data sheet
        serial_number = (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))
        self.i2c.writeto(self.addr, bytearray([MSER_REG]))
        sleep_ms(MEAS_DELAY)               # From the data sheet
        serial_number = serial_number * 256 + (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))
        self.i2c.writeto(self.addr, bytearray([LSER_REG]))
        sleep_ms(MEAS_DELAY)              # From the data sheet
        serial_number = serial_number * 256 + (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))
        return serial_number