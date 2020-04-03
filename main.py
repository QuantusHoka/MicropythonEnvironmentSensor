from machine import Pin, I2C
from hdc1080 import HDC1080

i2c = I2C(scl=Pin(22), sda=Pin(21))
sensor = HDC1080(i2c)

def temp():
    print(sensor.read_temperature())

def hum():
    print(sensor.read_humidity())