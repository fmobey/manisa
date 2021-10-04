# -----------------------------------------------------
# MicroZerr - ZerrGate Raspi
# Date of Issue : 29.05.21
# Version : 2.02
# -----------------------------------------------------
import os
import time
import sys
import paho.mqtt.client as mqtt
import json
import datetime
import smbus
import json
import socket
import subprocess
import Adafruit_CharLCD as LCD
import glob
# ----------------------------------------------------
import Adafruit_GPIO

# -----------------------------------------------------
# Import config.json
# -----------------------------------------------------
with open('/bin/zerosensor/config.json', 'r') as fp:
    obj = json.load(fp)
    THINGSBOARD_HOST = obj["TB_MQTT"]
    Sensor_SHT_token = obj["Sensor_SHT_token"]  # MQTT Token SHT
    Sensor_HTU_token = obj["Sensor_HTU_token"]  # MQTT Token SHT
    Sensor_Status0 = obj["Sensor_Status0"]  # MQTT Token DS18B20 1. cihaz
    Sensor_Status1 = obj["Sensor_Status1"]  # MQTT Token DS18B20 varsa 2. cihaz
    Sensor_Status2 = obj["Sensor_Status2"]  # MQTT Token DS18B20 varsa 2. cihaz
    IS_MAX_TB_TOKEN = obj['IS_MAX_TB_TOKEN']  # 1 MAX
    Is_Sensor_SHT = obj["Is_Sensor_SHT"]  # Enable or Disable
    Is_Sensor_HTU = obj["Is_Sensor_HTU"]  # Enable or Disable
    MAX_TEMP = obj['IS_Sensor_MAX31856']  # Enable or Disable
    POST_TIMER = obj["DATA_POST_TIME"] * 10
    NTP_IP = obj['NTP_IP']
    IS_PASSIVE = obj['IS_PASSIVE']

# -----------------------------------------------------
# Set Max31856 if available
# -----------------------------------------------------
if MAX_TEMP == 1:
    #    from Adafruit_MAX31856 import MAX31856 as MAX31856
    #    from MAX31856 import MAX31856
    software_spi = {"clk": 21, "cs": 16, "do": 19, "di": 17}
    sensor = MAX31856(software_spi=software_spi)

# -----------------------------------------------------
# Set SHT21 if available
# -----------------------------------------------------
if Is_Sensor_SHT == 1:
    import SHT21

# -----------------------------------------------------
# Set HTU21 if available
# -----------------------------------------------------
if Is_Sensor_HTU == 1:
    import HTU21

# -----------------------------------------------------
# LCD Pin Definations
# -----------------------------------------------------
lcd_rs = 25  # RS of LCD is connected to GPIO 7 on PI
lcd_en = 24  # EN of LCD is connected to GPIO 8 on PI
lcd_d4 = 23  # D4 of LCD is connected to GPIO 25 on PI
lcd_d5 = 17  # D5 of LCD is connected to GPIO 24 on PI
lcd_d6 = 18  # D6 of LCD is connected to GPIO 23 on PI
lcd_d7 = 22  # D7 of LCD is connected to GPIO 18 on PI
lcd_backlight = 0  # LED is not connected so we assign to 0

# ------------------------------------------------------
# LCD Definations
# -----------------------------------------------------
lcd_columns = 16  # for 16*2 LCD
lcd_rows = 2  # for 16*2 LCD
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows,
                           lcd_backlight)  # Send all the pin details to library
lcd.message('   MicroZerr \n')  # Give a intro message
get_ip_add = subprocess.Popen("hostname -I", shell=True, stdout=subprocess.PIPE).stdout
ip_add = get_ip_add.read()
lcd.message('%.14s' % (ip_add.decode()))  # Give a intro message
time.sleep(10)
lcd.message('%.14s' % (Sensor_HTU_token))
time.sleep(10)

# -----------------------------------------------------
# -----------------------------------------------------
send_time = 0


# -----------------------------------------------------
# Fonskiyonlar
# -----------------------------------------------------
def SHT_Enable():
    if Is_Sensor_SHT == 1:
        try:
            temp = SHT21.read_temperature()
            time.sleep(1)
            hum = SHT21.read_humidity()
            sensor_data = {'temperature': 0, 'humdity': 0, 'dtime': 0}
            try:
                client = mqtt.Client()
                client.username_pw_set(Sensor_SHT_token)
                client.connect(THINGSBOARD_HOST, 1883, 60)
                client.loop_start()
                sensor_data['temperature'] = temp
                sensor_data['humdity'] = hum
                sensor_data['dtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
                lcd.clear()  # Clear the LCD screen
                lcd.message(Sensor_SHT_token)
                lcd.message('\n%.9s' % datetime.datetime.now().strftime("%H:%M:%S"))
                lcd.message(' T:%.1f C \n' % temp)  # Display the value of temperature
                time.sleep(5)
                client.loop_stop()
                client.disconnect()
            except:
                print 'MQTT HATA'
        except:
            print 'SHT GENEL HATA'
            pass
    else:
        print 'SHT Disable'


def read_temp_ds18b20_bir():  # a function that grabs the raw temperature data from the sensor
    try:
        try:
            base_dir = '/sys/bus/w1/devices/'
            try:
                device_folder = glob.glob(base_dir + '28*')[0]  # 1. CIHAZ
            except IndexError:
                sys.stdout = open('/bin/zerosensor/debug', 'a')
                print 'cihaz yok'
                pass
            except:
                print 'Dosya Konumu Hatasi'
                pass
            device_file = device_folder + '/w1_slave'
            f = open(device_file, 'r')
            lines = f.readlines()
            f.close()
        except:
            print 'Dosya isim okuma hatasi DS18B20'

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0

            devicelist1 = os.listdir('/sys/bus/w1/devices')
            device_id = devicelist1[1]  # 0. eleman w1 - 1. eleman ds18b20 - 2. eleman ds18b20
            try:

                client = mqtt.Client()
                client.username_pw_set(Sensor_Status0)  # Status 0 = 1. cihaz
                client.connect(THINGSBOARD_HOST, 1883, 60)
                client.loop_start()
                sensor_data = {'temperature': 0, 'dtime': 0}
                sensor_data['temperature'] = temp_c
                sensor_data['dtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
                lcd.clear()  # Clear the LCD screen
                lcd.message(Sensor_Status0)  # Status 0 = 1. cihaz
                lcd.message('\n%.9s' % datetime.datetime.now().strftime("%H:%M:%S"))
                lcd.message(' T:%.1f C \n' % temp_c)  # Display the value of temperature
                time.sleep(5)
                client.loop_stop()
                client.disconnect()  # Status 0 = 1. cihaz
            except:
                print 'MQTT HATASI 1. CIHAZ'
            return temp_c, device_id, Sensor_Status0

    except:
        print '1. GENEL HATA'
        pass


def read_temp_ds18b20_iki():  # a function that grabs the raw temperature data from the sensor
    try:
        try:
            base_dir = '/sys/bus/w1/devices/'
            try:
                device_folder = glob.glob(base_dir + '28*')[1]  # 2. CIHAZ
            except IndexError:
                sys.stdout = open('/bin/zerosensor/debug', 'a')
                print 'cihaz yok'
                pass
            except:
                print 'something is wrong'
                pass
            device_file = device_folder + '/w1_slave'
            f = open(device_file, 'r')
            lines = f.readlines()
            f.close()
        except:
            print 'Dosya isim okuma hatasi DS18B20'

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0

            devicelist1 = os.listdir('/sys/bus/w1/devices')
            device_id = devicelist1[2]  # 0. eleman w1 - 1. eleman ds18b20 - 2. eleman ds18b20
            try:

                client = mqtt.Client()
                client.username_pw_set(Sensor_Status1)  # Status 1 = 2. cihaz
                client.connect(THINGSBOARD_HOST, 1883, 60)
                client.loop_start()
                sensor_data = {'temperature': 0, 'dtime': 0}
                sensor_data['temperature'] = temp_c
                sensor_data['dtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
                lcd.clear()  # Clear the LCD screen
                lcd.message(Sensor_Status1)  # Status 1 = 2. cihaz
                lcd.message('\n%.9s' % datetime.datetime.now().strftime("%H:%M:%S"))
                lcd.message(' T:%.1f C \n' % temp_c)  # Display the value of temperature
                time.sleep(5)
                client.loop_stop()
                client.disconnect()  # Status 1 = 2. cihaz
            except:
                print 'MQTT 2. CIHAZ'
            return temp_c, device_id, Sensor_Status1
    except:
        print '2. GENEL HATA'
        pass


def read_temp_ds18b20_uc():  # a function that grabs the raw temperature data from the sensor

    try:
        try:
            base_dir = '/sys/bus/w1/devices/'
            try:
                device_folder = glob.glob(base_dir + '28*')[2]  # 3. CIHAZ
            except IndexError:
                print 'cihaz yok'
                pass
            except:
                print 'something is wrong'
                pass
            device_file = device_folder + '/w1_slave'
            f = open(device_file, 'r')
            lines = f.readlines()
            f.close()
        except:
            print

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0

            devicelist1 = os.listdir('/sys/bus/w1/devices')
            device_id = devicelist1[3]  # 0. eleman w1 - 1. eleman ds18b20 - 2. eleman ds18b20 - 3. eleman ds18b20

            client = mqtt.Client()
            client.username_pw_set(Sensor_Status2)  # Status 2 = 3. cihaz
            client.connect(THINGSBOARD_HOST, 1883, 60)
            client.loop_start()
            sensor_data = {'temperature': 0, 'dtime': 0}
            sensor_data['temperature'] = temp_c
            sensor_data['dtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
            lcd.clear()  # Clear the LCD screen
            lcd.message(Sensor_Status2)  # Status 2 = 3. cihaz
            lcd.message('\n%.9s' % datetime.datetime.now().strftime("%H:%M:%S"))
            lcd.message(' T:%.1f C \n' % temp_c)  # Display the value of temperature
            time.sleep(5)
            client.loop_stop()
            client.disconnect()  # Status 2 = 3. cihaz
            return temp_c, device_id, Sensor_Status2
    except:
        print '3. cihaz okunamadi'
        pass


def max_sensor_temp():
    temp = sensor.read_temp_c()
    client = mqtt.Client()
    client.username_pw_set(IS_MAX_TB_TOKEN)  # MAX31856 TOKEN
    client.connect(THINGSBOARD_HOST, 1883, 60)
    client.loop_start()
    sensor_data = {'temperature': 0, 'dtime': 0}
    sensor_data['temperature'] = temp
    sensor_data['dtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
    lcd.clear()  # Clear the LCD screen
    lcd.message(IS_MAX_TB_TOKEN)  # MAX31856 LCD ISIM
    lcd.message('\n%.9s' % datetime.datetime.now().strftime("%H:%M:%S"))
    lcd.message(' T:%.1f C \n' % temp)  # Display the value of temperature
    time.sleep(5)
    client.loop_stop()
    client.disconnect()  # MAX31856 NAME
    return temp, IS_MAX_TB_TOKEN


def HTU_Enable():
    if Is_Sensor_HTU == 1:
        try:
            try:
                HTU21DF = HTU21()
                temp = HTU21DF.read_temperature()
                time.sleep(1)
                hum = HTU21DF.read_humidity()
                if hum > 100:
                    hum = hum - 22
            except:
                print 'HTU OKUNAMADI'

            sensor_data = {'temperature': 0, 'humdity': 0, 'dtime': 0}
            try:
                client = mqtt.Client()
                client.username_pw_set(Sensor_HTU_token)
                client.connect(THINGSBOARD_HOST, 1883, 60)
                client.loop_start()
                sensor_data['temperature'] = temp
                sensor_data['humdity'] = hum
                sensor_data['dtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
                lcd.clear()  # Clear the LCD screen
                lcd.message(Sensor_HTU_token)
                lcd.message('\n%.9s' % datetime.datetime.now().strftime("%H:%M:%S"))
                lcd.message(' T:%.1f C \n' % temp)  # Display the value of temperature
                time.sleep(5)
                client.loop_stop()
                client.disconnect()
            except:
                print 'MQTT HATA'
        except:
            print 'SHT GENEL HATA'
            pass
    else:
        print 'HTU Disable'


# -----------------------------------------------------
# -----------------------------------------------------
try:
    while True:
        currentMillis = time.time()

        if (currentMillis - send_time) > POST_TIMER:
            send_time = currentMillis

            lcd.clear()  # Clear the LCD screen
            lcd.message('   MicroZerr \n')  # Give a intro message
            lcd.message('  %.14s' % (ip_add.decode()))  # Give a intro message
            time.sleep(8)

            try:
                if MAX_TEMP == 1:
                    max_sensor_temp()
                    time.sleep(20)

                DS_number_devicelist = os.listdir('/sys/bus/w1/devices')
                if len(DS_number_devicelist) == 1:
                    SHT_Enable()
                    HTU_Enable()
                    time.sleep(10)
                if len(DS_number_devicelist) == 2:
                    SHT_Enable()
                    HTU_Enable()
                    read_temp_ds18b20_bir()
                    time.sleep(10)
                if len(DS_number_devicelist) == 3:
                    SHT_Enable()
                    HTU_Enable()
                    read_temp_ds18b20_bir()
                    read_temp_ds18b20_iki()
                    time.sleep(10)
                if len(DS_number_devicelist) == 4:
                    SHT_Enable()
                    HTU_Enable()
                    read_temp_ds18b20_bir()
                    read_temp_ds18b20_iki()
                    read_temp_ds18b20_uc()
                    time.sleep(10)

            except:
                print 'Dosya okuma w1 device kaynakli problem WHILE ERROR'
                lcd.clear()  # Clear the LCD screen
                lcd.message('HATA IP KONTROL\n')  # Give a intro message
                lcd.message(' %.14s' % (ip_add.decode()))  # Give a intro message
                SHT_Enable()

        time.sleep(5)

except KeyboardInterrupt:
    lcd.clear()  # Clear the LCD screen
    lcd.message('  HATA \n')  # Give a intro message
    lcd.message(' %.14s' % (ip_add.decode()))  # Give a intro message
    time.sleep(100)
    pass
except:
    print 'DONGU GENEL HATASI'
    lcd.clear()  # Clear the LCD screen
    lcd.message('  HATA \n')  # Give a intro message
    lcd.message(' %.14s' % (ip_add.decode()))  # Give a intro message
    time.sleep(100)
    pass
