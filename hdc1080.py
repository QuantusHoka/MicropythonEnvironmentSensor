# Driver for the Texas Instruments HDC1080 temperature and humidity sensor
# Communication is done over I2C

from micropython import const
from machine import I2C
from time import sleep

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

HDC1080_CONFIG_RESET_BIT =                      const(0x8000)
HDC1080_CONFIG_HEATER_ENABLE =                  const(0x2000)
HDC1080_CONFIG_ACQUISITION_MODE =               const(0x1000)
HDC1080_CONFIG_BATTERY_STATUS =                 const(0x0800)
HDC1080_CONFIG_TEMPERATURE_RESOLUTION =         const(0x0400)
HDC1080_CONFIG_HUMIDITY_RESOLUTION_HBIT =       const(0x0200)
HDC1080_CONFIG_HUMIDITY_RESOLUTION_LBIT =       const(0x0100)

HDC1080_CONFIG_TEMPERATURE_RESOLUTION_14BIT =   const(0x0000)
HDC1080_CONFIG_TEMPERATURE_RESOLUTION_11BIT =   const(0x0400)

HDC1080_CONFIG_HUMIDITY_RESOLUTION_14BIT =      const(0x0000)
HDC1080_CONFIG_HUMIDITY_RESOLUTION_11BIT =      const(0x0100)
HDC1080_CONFIG_HUMIDITY_RESOLUTION_8BIT =       const(0x0200)


class HDC1080:
    def __init__(self, i2c, slave_addr=HDC1080_ADDR ):
        """Initialize a HDC1080 temperature and humidity sensor.
        Keyword arguments:
        i2c -- The i2c object (driver) used to interact through device addresses.
        slave_addr -- The slave address of the sensor (default 64 or 0x40).
        """
        self.i2c = i2c
        assert slave_addr in self.i2c.scan(), "Did not find slave %d in scan" % slave_addr
        self.addr = slave_addr
        # received data from temperature and humidity registers is two unsigned characters
        self.fmt = '>2B'
        # Sleep for 15 ms to allow the temperature and humidity temperatures to start recording
        # Only serial number registers 0xFB and 0xFF are available at first
        sleep(0.015)
        # set up for 14 bit resolution (in config register) for both temperature and humidity readings
        # independent measurements for now
        data = bytearray(3)
        data[0] = CONF_REG
        data[1] = 1 << 4
        i2c.writeto(self.addr, data)

    def read_temperature(self):
        """ Read the temperature
        Keyword arguments:
        celsius -- If the data is kept as celsius after reading (default False)
        """
        # write to the pointer register, changing it to the temperature register
        self.i2c.writeto(self.addr, bytearray([TEMP_REG]))
        # TODO: Waiting for a temperature update here may not be necessary, based on 14-bit resolution
        #sleep(0.0635)
        # per the spec, the conversion to celsius is (value / (2 ** 16)) * 165 - 40
        return ((int.from_bytes(self.i2c.readfrom(self.addr, 2), "big")) * 165 / 65536 - 40)

    def read_humidity(self):
        """ Read the relative humidity """
        # write to the pointer register, changing it to the humidity register
        self.i2c.writeto(self.addr, bytearray([HUMI_REG]))
        # TODO: Waiting for a humidity update here may not be necessary, based on 14-bit resolution
        #sleep(0.065)
        return ((int.from_bytes(self.i2c.readfrom(self.addr, 2), "big")) / 65536 * 100) # conversion per the spec

    def read_configuration_register(self):
        self.i2c.writeto(self.addr, bytearray([CONF_REG]))
        #sleep(0.0625)
        return (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))

    def turnHeaterOn(self):
        config_data = bytearray(3)
        config_data[0] = CONF_REG
        config_data[1] = self.read_configuration_register()
        config_data[1] = config_data | HDC1080_CONFIG_HEATER_ENABLE 
        i2c.writeto(self.addr, config_data)
        return

    def turnHeaterOff(self):
        config_data = bytearray(3)
        config_data[0] = CONF_REG
        config_data[1] = self.read_configuration_register()
        config_data[1] = (config_data & ~HDC1080_CONFIG_HEATER_ENABLE) >> 8
        i2c.writeto(self.addr, config_data)
        return

    def setHumidityResolution(self,resolution):
        config_data = bytearray(3)
        config_data[0] = CONF_REG
        config_data[1] = self.read_configuration_register()
        config_data[1] = ((config_data & ~0x300) | resolution) >> 8 
        i2c.writeto(self.addr, config_data)
        return

    def setTemperatureResolution(self,resolution):
        config_data = bytearray(3)
        config_data[0] = CONF_REG
        config_data[1] = self.read_configuration_register()
        config_data[1] = ((config_data & ~0x0400) | resolution) >> 8 
        i2c.writeto(self.addr, config_data)
        return

    def readManufacturerID(self):
        self.i2c.writeto(self.addr, bytearray([MFID_REG]))
        #sleep(0.0625)              # From the data sheet
        return (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))

    def readDeviceID(self):
        self.i2c.writeto(self.addr, bytearray([DVID_REG]))
        #sleep(0.0625)              # From the data sheet
        return (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))

    def readSerialNumber(self):
        self.i2c.writeto(self.addr, bytearray([FSER_REG]))
        #sleep(0.0625)              # From the data sheet
        serial_number = (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))
        self.i2c.writeto(self.addr, bytearray([MSER_REG]))
        #sleep(0.0625)              # From the data sheet
        serial_number = serial_number * 256 + (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))
        self.i2c.writeto(self.addr, bytearray([LSER_REG]))
        #sleep(0.0625)              # From the data sheet
        serial_number = serial_number * 256 + (int.from_bytes(self.i2c.readfrom(self.addr, 2), "big"))
        return serial_number