from machine import Pin, PWM, Timer, ADC
import time, math

def display(count):
    
    if(count>9999):
        return
    
    print(count)
        
    D4 = count % 10
    D3 = (count//10) % 10
    D2 = (count//100) % 10
    D1 = count//1000
    
    dp = Pin(0, Pin.OUT,Pin.PULL_DOWN)
    d1 = Pin(1, Pin.OUT,Pin.PULL_DOWN)
    d2 = Pin(2, Pin.OUT,Pin.PULL_DOWN) 
    d3 = Pin(3, Pin.OUT,Pin.PULL_DOWN)
    d4 = Pin(4, Pin.OUT,Pin.PULL_DOWN) 
    a = Pin(5, Pin.OUT) 
    b = Pin(6, Pin.OUT) 
    c = Pin(7, Pin.OUT)
    d = Pin(8, Pin.OUT) 
    e = Pin(9, Pin.OUT)
    f = Pin(10, Pin.OUT) 
    g = Pin(11, Pin.OUT) 
    
    pins = [g,f,e,d,c,b,a]
    
    values = {0:[0,1,1,1,1,1,1],
            1:[0,0,0,0,1,1,0],
            2:[1,0,1,1,0,1,1],
            3:[1,0,0,1,1,1,1],
            4:[1,1,0,0,1,1,0],
            5:[1,1,0,1,1,0,1],
            6:[1,1,1,1,1,0,1],
            7:[0,0,0,0,1,1,1],
            8:[1,1,1,1,1,1,1],
            9:[1,1,0,1,1,1,1]
        }
    
    d3.value(1)
    d1.value(1)
    d2.value(1)
    d4.value(1)
        
    for index, value in enumerate(values[D1]):
        pins[index].value(value)
        d1.value(0)
        dp.value(0)
        
    time.sleep(0.002)
        
    d3.value(1)
    d1.value(1)
    d2.value(1)
    d4.value(1)
    
    for index, value in enumerate(values[D2]):
        pins[index].value(value)
        d2.value(0)
        dp.value(1)
        
    time.sleep(0.002)
        
    d3.value(1)
    d1.value(1)
    d2.value(1)
    d4.value(1)
        
    for index, value in enumerate(values[D3]):
        pins[index].value(value)
        d3.value(0)
        dp.value(0)
        
    time.sleep(0.002)    
    
    d3.value(1)
    d1.value(1)
    d2.value(1)
    d4.value(1)
    
    for index, value in enumerate(values[D4]):
        pins[index].value(value)
        d4.value(0)
        dp.value(0)
    
    time.sleep(0.002)


adc = ADC(Pin(28))

R_fixed = 20 # change based on empirical.
V_p = 3.3265 # change to empirical reading of GPIO.OUT pin for thermistor, use Voltmeter

A = Pin(27, Pin.IN, Pin.PULL_DOWN)
B = Pin(26, Pin.IN, Pin.PULL_DOWN)
setpoint = 0
settingMode = False

prev = 0;
# Can change the value to increment/decrement more heavily/lightly
lookup_table = {(0,1): 0.5, (0,2): -0.5,(1,0): -0.5, (1,3): 0.5,(3,1): -0.5, (3,2): 0.5,(2,0): 0.5, (2,3): -0.5}

fet = Pin(22)
#fet.freq(732)

startTime = time.time()
prevTime = 0

a = 0
e_prev = 0
prevPIDTime = 0
K = 1
Ti = 1
Td = 1

temp_time = 0

while True:
    
    # calibration code
    #with open('tempCalibration3.txt', 'w') as file: #cal1 at 41 C,  #cal2 at 67 C, # cal3 at 21 C
        #for i in range(30):
            #V_Rfixed = (adc.read_u16()/65535) * V_p
            #R_thermistor = R_fixed* ((V_p/V_Rfixed) - 1)
            #print("R: " + str(R_thermistor))
            #file.write(str(R_thermistor) + "\n")
            #time.sleep(1)
    #break
    
    V_Rfixed = (adc.read_u16()/65535) * V_p
    R_thermistor = R_fixed* ((V_p/V_Rfixed) - 1)
    current = V_p/(R_fixed + R_thermistor)
    res_heating = 1000*(current**2*R_thermistor)/8
    print(res_heating)
    print(R_thermistor)
    
    # Steinhart-hart calibration for NTC thermistor

    if(time.time()-temp_time > 1):
        Temp = (1 / (0.0028427564207573488 + 0.000338027116557912 * math.log(R_thermistor) + 0.00000555342539196426 * (math.log(R_thermistor))**3)) - res_heating - 273.15
        temp_time = time.time()
    print(round(Temp*100))
    tempTime = time.time()
    # can adjust the value to get data in more or less resolution/precision
    if((time.time() - prevTime) > 0.5 or prevTime == 0):
        with open('data.txt', 'w') as file:
            file.write(str(Temp) + ", " + str(tempTime-startTime) + ", " + str(R_thermistor) + "\n")
        prevTime = time.time()
        
    AB = (A.value() << 1) | B.value()
    
    # if you turn knob to negative, it will display weird values
    if(AB != prev):
        settingMode = True
        setpoint = setpoint + lookup_table[(prev, AB)]
        display(round(setpoint*100))
        prev = AB
        lastSetTime = time.time()
    elif(settingMode):
        # Can change duration to optimize UX
        display(round(setpoint*100))
        if(time.time()-lastSetTime > 0.5):
            settingMode = False
    else:
        display(round(Temp*100))
    
    # The time iteration for integral and derivative must be greater than the time per cycle of while loop.
    e_now = Temp - setpoint
    if((time.time() - prevPIDTime) > 0.1 or prevPIDTime == 0):
        timeChange = (time.time() - prevPIDTime)
        a = a + e_now * timeChange
        d = (e_now - e_prev)/ timeChange
        prevPIDtime = time.time()
        e_prev = e_now
    
        
    # TODO:
    # 1. implement another time action with the encoder to set phases of setting and displaying
    # 2. use time to get the area and the derivative
    # 3. code the pin for the mosfet
    # 4. Matplotlib to graph the data
    # 5. with the reapsbery pi get the time to iterate the action loop.
        
    
    
#     output = round(K*(e_now + (1/Ti)*a + Td*d))
#     duty = int(0.9 * 65535)
#     fet.duty_u16(duty)
    
    fet.value(1)
    

    
    # matplot lib and numpy to graph T vs t data for PID tuning!






