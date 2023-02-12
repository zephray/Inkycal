# *****************************************************************************
# * | File        :	  epd7in5bc.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V4.0
# * | Date        :   2019-06-20
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


import logging
from inkycal.display.drivers import epdconfig

# Display resolution
EPD_WIDTH = 960
EPD_HEIGHT = 768

CHIP_MASTER = 0
CHIP_SLAVE = 1
CHIP_BOTH = 2

class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.cs2_pin = epdconfig.CS2_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    # Hardware reset
    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(10)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)
    
    def send_byte(self, byte, chip):
        if ((chip == CHIP_MASTER) or (chip == CHIP_BOTH)):
            epdconfig.digital_write(self.cs_pin, 0)
        if ((chip == CHIP_SLAVE) or (chip == CHIP_BOTH)):
            epdconfig.digital_write(self.cs2_pin, 0)
        if (chip == CHIP_SLAVE):
            epdconfig.spi2_writebyte([byte])
        else:
            epdconfig.spi_writebyte([byte])
        epdconfig.digital_write(self.cs_pin, 1)
        epdconfig.digital_write(self.cs2_pin, 1)

    def send_command(self, command, chip = CHIP_BOTH):
        epdconfig.digital_write(self.dc_pin, 0)
        self.send_byte(command, chip)

    def send_data(self, data, chip = CHIP_BOTH):
        epdconfig.digital_write(self.dc_pin, 1)
        self.send_byte(data, chip)

    def send_bulk_data(self, data, chip = CHIP_BOTH):
        epdconfig.digital_write(self.dc_pin, 1)
        if ((chip == CHIP_MASTER) or (chip == CHIP_BOTH)):
            epdconfig.digital_write(self.cs_pin, 0)
        if ((chip == CHIP_SLAVE) or (chip == CHIP_BOTH)):
            epdconfig.digital_write(self.cs2_pin, 0)
        if (chip == CHIP_SLAVE):
            epdconfig.spi2_writebyte(data)
        else:
            epdconfig.spi_writebyte(data)
        epdconfig.digital_write(self.cs_pin, 1)
        epdconfig.digital_write(self.cs2_pin, 1)

    def ReadBusy(self):
        logging.debug("e-Paper busy")
        while (epdconfig.digital_read(self.busy_pin) == 0):  # 0: idle, 1: busy
            epdconfig.delay_ms(100)
        logging.debug("e-Paper busy release")

    def init(self):
        print("epd init")

        if (epdconfig.module_init() != 0):
            return -1

        self.reset()

        self.send_command(0x05)
        self.send_data(0x7d)
        
        epdconfig.delay_ms(200)

        self.send_command(0x05)
        self.send_data(0x00)

        epdconfig.delay_ms(10)

        self.send_command(0xd8)
        self.send_data(0x80)
        self.send_command(0xd6)
        self.send_data(0x00)
        self.send_command(0xa7)
        self.send_data(0x10)

        epdconfig.delay_ms(100)

        self.send_command(0xa7)
        self.send_data(0x00)
        
        epdconfig.delay_ms(100)

        self.send_command(0x03)
        self.send_data(0x00)
        self.send_data(0x11)

        self.send_command(0x44, chip=CHIP_MASTER)
        self.send_data(0x00, chip=CHIP_MASTER)
        self.send_command(0x45, chip=CHIP_MASTER)
        self.send_data(0x80, chip=CHIP_MASTER)
        self.send_command(0xa7, chip=CHIP_MASTER)
        self.send_data(0x10, chip=CHIP_MASTER)
        epdconfig.delay_ms(100)
        self.send_command(0xa7, chip=CHIP_MASTER)
        self.send_data(0x00, chip=CHIP_MASTER)
        epdconfig.delay_ms(100)

        self.send_command(0x44, chip=CHIP_MASTER)
        self.send_data(0x06, chip=CHIP_MASTER)
        self.send_command(0x45, chip=CHIP_MASTER)
        self.send_data(0x82, chip=CHIP_MASTER)
        self.send_command(0xa7, chip=CHIP_MASTER)
        self.send_data(0x10, chip=CHIP_MASTER)
        epdconfig.delay_ms(100)
        self.send_command(0xa7, chip=CHIP_MASTER)
        self.send_data(0x00, chip=CHIP_MASTER)
        epdconfig.delay_ms(100)

        self.send_command(0x44, chip=CHIP_SLAVE)
        self.send_data(0x00, chip=CHIP_SLAVE)
        self.send_command(0x45, chip=CHIP_SLAVE)
        self.send_data(0x80, chip=CHIP_SLAVE)
        self.send_command(0xa7, chip=CHIP_SLAVE)
        self.send_data(0x10, chip=CHIP_SLAVE)
        epdconfig.delay_ms(100)
        self.send_command(0xa7, chip=CHIP_SLAVE)
        self.send_data(0x00, chip=CHIP_SLAVE)
        epdconfig.delay_ms(100)

        self.send_command(0x44, chip=CHIP_SLAVE)
        self.send_data(0x06, chip=CHIP_SLAVE)
        self.send_command(0x45, chip=CHIP_SLAVE)
        self.send_data(0x82, chip=CHIP_SLAVE)
        self.send_command(0xa7, chip=CHIP_SLAVE)
        self.send_data(0x10, chip=CHIP_SLAVE)
        epdconfig.delay_ms(100)
        self.send_command(0xa7, chip=CHIP_SLAVE)
        self.send_data(0x00, chip=CHIP_SLAVE)
        epdconfig.delay_ms(100)

        self.send_command(0x60) # TCON
        self.send_data(0x25)
        self.send_command(0x61, chip=CHIP_MASTER) # STV_DIR
        self.send_data(0x01)
        self.send_command(0x02) # VCOM
        self.send_data(0x00)

        print("epd init done")

        return 0

    def poweron(self):
        print("epd power on")
        self.send_command(0x51)
        self.send_data(0x50)
        self.send_data(0x01)
        for i in range(1, 5):
            self.send_command(0x09)
            self.send_data(0x1f)
            self.send_command(0x51)
            self.send_data(0x50)
            self.send_data(i)
            self.send_command(0x09)
            self.send_data(0x9f)
            epdconfig.delay_ms(2)
        for i in range(1, 11):
            self.send_command(0x09)
            self.send_data(0x1f)
            self.send_command(0x51)
            self.send_data(0x0a)
            self.send_data(i)
            self.send_command(0x09)
            self.send_data(0x9f)
            epdconfig.delay_ms(2)
        for i in range(3, 11):
            self.send_command(0x09)
            self.send_data(0x7f)
            self.send_command(0x51)
            self.send_data(0x0a)
            self.send_data(i)
            self.send_command(0x09)
            self.send_data(0xff)
            epdconfig.delay_ms(2)
        for i in range(9, 1, -1):
            self.send_command(0x09)
            self.send_data(0x7f)
            self.send_command(0x51)
            self.send_data(i)
            self.send_data(0x0a)
            self.send_command(0x09)
            self.send_data(0xff)
            epdconfig.delay_ms(2)
        self.send_command(0x09)
        self.send_data(0xff)
        epdconfig.delay_ms(10)
        print("epd power on done")

    def poweroff(self):
        print("epd power off")
        self.ReadBusy()
        self.send_command(0x09)
        self.send_data(0x7f)
        self.send_command(0x05)
        self.send_data(0x7d)
        self.send_command(0x09)
        self.send_data(0x00)
        epdconfig.delay_ms(200)
        self.ReadBusy()
        print("epd power off done")

    def getbuffer(self, image):
        # logging.debug("bufsiz = ",int(self.width/8) * self.height)
        buf = [0x00] * (int(self.width / 8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        logging.debug('imwidth = %d  imheight =  %d ', imwidth, imheight)
        if (imwidth == self.width and imheight == self.height):
            logging.debug("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[int((x + y * self.width) / 8)] |= 0x80 >> (x % 8)
        elif (imwidth == self.height and imheight == self.width):
            logging.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[int((newx + newy * self.width) / 8)] |= 0x80 >> (y % 8)
        return buf

    def display(self, imageblack, imagered):
        print("epd display")
        self.send_command(0x13)
        self.send_data(0x00)
        self.send_data(0x3b)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xff)
        self.send_data(0x02)

        self.send_command(0x90)
        self.send_data(0x00)
        self.send_data(0x3b)
        self.send_data(0x00)
        self.send_data(0xc1)

        self.send_command(0x12)
        self.send_data(0x3b)
        self.send_data(0x00)
        self.send_data(0x14)

        self.send_command(0x10)
        for y in range(0, self.height):
            start = y * self.width // 8
            length = self.width // 16
            self.send_bulk_data(imageblack[start: start+length], chip=CHIP_MASTER)
            start = start + length
            self.send_bulk_data(imageblack[start: start+length], chip=CHIP_SLAVE)
        
        self.send_command(0x12)
        self.send_data(0x3b)
        self.send_data(0x00)
        self.send_data(0x14)

        self.send_command(0x11)
        for y in range(0, self.height):
            start = y * self.width // 8 
            length = self.width // 16
            self.send_bulk_data(imagered[start: start+length], chip=CHIP_MASTER)
            start = start + length
            self.send_bulk_data(imagered[start: start+length], chip=CHIP_SLAVE)
        

        self.poweron()
        self.ReadBusy()
        self.send_command(0x15)  # display refresh
        self.send_data(0x3c)
        epdconfig.delay_ms(100)
        self.ReadBusy()
        print("epd display done")

    def Clear(self):
        print("epd clear")
        self.send_command(0x13)
        self.send_data(0x00)
        self.send_data(0x3b)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xff)
        self.send_data(0x02)

        self.send_command(0x90)
        self.send_data(0x00)
        self.send_data(0x3b)
        self.send_data(0x00)
        self.send_data(0xc1)

        self.send_command(0x12)
        self.send_data(0x3b)
        self.send_data(0x00)
        self.send_data(0x14)

        self.send_command(0x10)
        for i in range(0, int(self.width / 16 * self.height)):
            self.send_data(0x00)
        
        self.send_command(0x12)
        self.send_data(0x3b)
        self.send_data(0x00)
        self.send_data(0x14)

        self.send_command(0x11)
        for i in range(0, int(self.width / 16 * self.height)):
            self.send_data(0x00)

        self.poweron()
        self.ReadBusy()
        self.send_command(0x15)  # display refresh
        self.send_data(0x3c)
        epdconfig.delay_ms(100)
        self.ReadBusy()
        print("epd clear done")

    def sleep(self):
        self.poweroff()
        self.send_command(0x09)
        self.send_data(0x7f)
        self.send_data(0x7d)
        self.send_data(0x00)
        self.ReadBusy()

        epdconfig.module_exit()
### END OF FILE ###
