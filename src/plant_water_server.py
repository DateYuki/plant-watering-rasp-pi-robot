import RPi.GPIO as GPIO
import time
import datetime as dt
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class PlantWaterServer:

    PUMP_RELAY_PIN = 17 
    PLANT_1_VALVE_RELAY_PIN = 18 
    PLANT_2_VALVE_RELAY_PIN = 27

    i2c      = busio.I2C(board.SCL, board.SDA)
    ads      = ADS.ADS1115(i2c)
    ads.gain = 2 / 3
    chan     = AnalogIn(ads, ADS.P0)

    SAMPLINGTIME  = 0.01 #[s]
    MAX_VOLTAGE   = 5.0  #[v](flow-sensor's spec)
    MAX_FLOW_RATE = 100  #[ml/s] (flow-sensor's spec)

    plant_1_day_of_interval = 10    #[day]
    plant_1_water_quantity  = 100  #[ml]
    
    plant_2_day_of_interval = 10   #[day]
    plant_2_water_quantity  = 100  #[ml]

    plant_1_day_count_since_last_watering = 0 #[day]
    plant_2_day_count_since_last_watering = 0 #[day]

    def rasp_pi_init(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PUMP_RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.PLANT_1_VALVE_RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.PLANT_2_VALVE_RELAY_PIN, GPIO.OUT)

    def rasp_pi_dispose(self):
        GPIO.cleanup()

    def updatePlant1Setting(self, new_day_of_interval, new_plant_water_quantity):
        is_changed_setting = False
        if (self.plant_1_day_of_interval != new_day_of_interval):
            self.plant_1_day_of_interval = new_day_of_interval
            self.plant_1_day_count_since_last_watering = 1
            is_changed_setting = True
        elif (self.plant_1_water_quantity != new_plant_water_quantity):
            self.plant_1_water_quantity = new_plant_water_quantity
            is_changed_setting = True
        return is_changed_setting

    def updatePlant2Setting(self, new_day_of_interval, new_plant_water_quantity):
        is_changed_setting = False
        if (self.plant_2_day_of_interval != new_day_of_interval):
            self.plant_2_day_of_interval = new_day_of_interval
            self.plant_2_day_count_since_last_watering = 1
            is_changed_setting = True
        elif (self.plant_2_water_quantity != new_plant_water_quantity):
            self.plant_2_water_quantity = new_plant_water_quantity
            is_changed_setting = True
        return is_changed_setting
    
    def getDateTimeOfNextPlant1Watering(self):
        now = dt.datetime.now()
        nextDateTimeOfNextPlantWatering = dt.datetime(now.year, now.month, now.day)
        if (now.hour < 10):
            nextDateTimeOfNextPlantWatering = nextDateTimeOfNextPlantWatering + dt.timedelta(days = self.plant_1_day_of_interval - self.plant_1_day_count_since_last_watering)
        else:
            nextDateTimeOfNextPlantWatering = nextDateTimeOfNextPlantWatering + dt.timedelta(days = self.plant_1_day_of_interval - self.plant_1_day_count_since_last_watering + 1)
        return nextDateTimeOfNextPlantWatering.strftime('%m/%d')
    
    def getDateTimeOfNextPlant2Watering(self):
        now = dt.datetime.now()
        nextDateTimeOfNextPlantWatering = dt.datetime(now.year, now.month, now.day)
        if (now.hour < 10):
            nextDateTimeOfNextPlantWatering = nextDateTimeOfNextPlantWatering + dt.timedelta(days = self.plant_2_day_of_interval - self.plant_2_day_count_since_last_watering)
        else:
            nextDateTimeOfNextPlantWatering = nextDateTimeOfNextPlantWatering + dt.timedelta(days = self.plant_2_day_of_interval - self.plant_2_day_count_since_last_watering + 1)
        return nextDateTimeOfNextPlantWatering.strftime('%m/%d')
    
    def incrementPlant1DayCount(self):
        self.plant_1_day_count_since_last_watering += 1

    def incrementPlant2DayCount(self):
        self.plant_2_day_count_since_last_watering += 1
    
    def plant1Watering(self):
        try:
            self.rasp_pi_init
            flow_time = 0 #[s]
            water_quantity = 0 #[ml]
            raw_flow_rate_values_for_adition_average = [0, 0, 0, 0, 0] #[ml/s]
            GPIO.output(self.PLANT_1_VALVE_RELAY_PIN, True)
            GPIO.output(self.PUMP_RELAY_PIN, True)
            while water_quantity < self.plant_1_water_quantity:
                flow_time += self.SAMPLINGTIME
                voltage = self.chan.voltage
                raw_flow_rate = voltage / self.MAX_VOLTAGE * self.MAX_FLOW_RATE
                del raw_flow_rate_values_for_adition_average[0]
                raw_flow_rate_values_for_adition_average += [raw_flow_rate]
                sum_flow_rate = 0
                for flowRateValue in raw_flow_rate_values_for_adition_average:
                    sum_flow_rate += flowRateValue
                ave_flow_rate = sum_flow_rate / len(raw_flow_rate_values_for_adition_average)
                water_quantity += ave_flow_rate * self.SAMPLINGTIME
                time.sleep(self.SAMPLINGTIME)
            GPIO.output(self.PLANT_1_VALVE_RELAY_PIN, False)
            GPIO.output(self.PUMP_RELAY_PIN, False)
            self.plant_1_day_count_since_last_watering = 1
        except Exception:
            self.rasp_pi_dispose
            self.rasp_pi_init
    
    def plant2Watering(self):
        try:
            flow_time = 0 #[s]
            water_quantity = 0 #[ml]
            raw_flow_rate_values_for_adition_average = [0, 0, 0, 0, 0] #[ml/s]
            GPIO.output(self.PLANT_2_VALVE_RELAY_PIN, True)
            GPIO.output(self.PUMP_RELAY_PIN, True)
            while water_quantity < self.plant_2_water_quantity:
                flow_time += self.SAMPLINGTIME
                voltage = self.chan.voltage
                raw_flow_rate = voltage / self.MAX_VOLTAGE * self.MAX_FLOW_RATE
                del raw_flow_rate_values_for_adition_average[0]
                raw_flow_rate_values_for_adition_average += [raw_flow_rate]
                sum_flow_rate = 0
                for flowRateValue in raw_flow_rate_values_for_adition_average:
                    sum_flow_rate += flowRateValue
                ave_flow_rate = sum_flow_rate / len(raw_flow_rate_values_for_adition_average)
                water_quantity += ave_flow_rate * self.SAMPLINGTIME
                time.sleep(self.SAMPLINGTIME)
            GPIO.output(self.PLANT_2_VALVE_RELAY_PIN, False)
            GPIO.output(self.PUMP_RELAY_PIN, False)
            self.plant_2_day_count_since_last_watering = 1
        except Exception:
            self.rasp_pi_dispose
            self.rasp_pi_init
