import RPI.GPIO as GPIO
import time
import datetime as dt
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import Analogin

PUMP_RELAY_PIN = 17 
PLANT_1_VALVE_RELAY_PIN= 18 
PLANT_2_VALVE_RELAY_PIN = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_RELAY_PIN, GPIO.OUT)
GPIO.setup(PLANT_1_VALVE_RELAY_PIN, GPIO.OUT)
GPIO.setup(PLANT_2_VALVE_RELAY_PIN, GPIO.OUT)

try:
    GPIO.output(PLANT_1_VALVE_RELAY_PIN, False)
    GPIO.output(PLANT_2_VALVE_RELAY_PIN, False)
    GPIO.output(PUMP_RELAY_PIN, False)
    
    i2c      = busio.I2C(board.SCL, board.SDA)
    ads      = ADS.ADS1115(i2c)
    ads.gain = 2 / 3
    chan     = Analogin(ads, ADS.PO)

    SAMPLINGTIME  = 0.01 #[s]
    MAX_VOLTAGE   = 4.5 #[v](flow-sensor's spec)
    MAX_FLOW_RATE = 100 #[ml/s] (flow-sensor's spec)

    PLANT_1_DAY_OF_INTERVAL = 7   #[day]
    PLANT_2_DAY_OF_INTERVAL = 10  #[day]
    PLANT_1_MAX_FLOW_TIME   = 6.0 #[s]
    PLANT_2_MAX_FLOW_TIME   = 12.0 #[s]
    PLANT_1_WATER_QUANTITY  = 200 #[ml]
    PLANT_2_WATER_QUANTITY  = 400 #[ml]

    plant1DayOfIntervalCount = 0
    plant2DayOfIntervalCount = 0

    while True:
        #-------- Plant-1 --------
        if PLANT_1_DAY_OF_INTERVAL <= plant1DayOfIntervalCount:
            flowTime = 0 #[s]
            waterQuantity = 0 #[ml]
            rawFlowRateValuesForAditionAverage = [0, 0, 0, 0, 0] #[ml/s]
            GPIO.output(PLANT_1_VALVE_RELAY_PIN, True)
            GPIO.output(PUMP_RELAY_PIN, True)
            while flowTime < PLANT_1_MAX_FLOW_TIME and waterQuantity < PLANT_1_WATER_QUANTITY:
                flowTime += SAMPLINGTIME
                voltage = chan.voltage
                rawFlowRate = voltage / MAX_VOLTAGE * MAX_FLOW_RATE
                del rawFlowRateValuesForAditionAverage[0]
                rawFlowRateValuesForAditionAverage += [rawFlowRate]
                sumFlowRate = 0
                for flowRateValue in rawFlowRateValuesForAditionAverage:
                    sumFlowRate += flowRateValue
                aveFlowRate = sumFlowRate / len(rawFlowRateValuesForAditionAverage)
                waterQuantity += aveFlowRate * SAMPLINGTIME
                time.sleep(SAMPLINGTIME)
            GPIO.output(PLANT_1_VALVE_RELAY_PIN, False)
            GPIO.output(PUMP_RELAY_PIN, False)
            plant1DayOfIntervalCount = 1
        else:
            plant1DayOfIntervalCount += 1
        #-------- Plant-2 --------
        if PLANT_2_DAY_OF_INTERVAL <= plant2DayOfIntervalCount:
            flowTime      = 0 #[s]
            waterQuantity = 0 #[ml]
            rawFlowRateValuesForAditionAverage = [0, 0, 0, 0, 0] #[ml/s]
            GPIO.output(PLANT_2_VALVE_RELAY_PIN, True)
            GPIO.output(PUMP_RELAY_PIN, True)
            while flowTime < PLANT_2_MAX_FLOW_TIME and waterQuantity < PLANT_2_WATER_QUANTITY:
                flowTime += SAMPLINGTIME
                voltage = chan.voltage
                rawFlowRate = voltage / MAX_VOLTAGE * MAX_FLOW_RATE
                del rawFlowRateValuesForAditionAverage[0]
                rawFlowRateValuesForAditionAverage += [rawFlowRate]
                sumFlowRate = 0
                for flowRateValue in rawFlowRateValuesForAditionAverage:
                    sumFlowRate += flowRateValue
                aveFlowRate = sumFlowRate / len(rawFlowRateValuesForAditionAverage)
                waterQuantity += aveFlowRate * SAMPLINGTIME
                time.sleep(SAMPLINGTIME)
            GPIO.output(PLANT_2_VALVE_RELAY_PIN, False)
            GPIO.output(PUMP_RELAY_PIN, False)
            plant2DayOfIntervalCount = 1
        else:
            plant2DayOfIntervalCount += 1
        #-------- wait to next day at 10:00 AM --------
        now = dt.datetime.now()
        nextDateTime = dt.datetime(now.year, now.month, now.day, 10)
        nextDateTime = nextDateTime + dt.timedelta(days = 1)
        waitDateTime = nextDateTime - now
        waitSeconds = waitDateTime.total_seconds()
        time.sleep(waitSeconds)
finally:
    GPIO.cleanup()
