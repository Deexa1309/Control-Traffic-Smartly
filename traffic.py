# LAG
# NO. OF VEHICLES IN SIGNAL CLASS
# stops not used
# DISTRIBUTION
# BUS TOUCHING ON TURNS
# Distribution using python class

# *** IMAGE XY COOD IS TOP LEFT
import random
import math
import time
import threading
# from vehicle_detection import detection
import pygame
import sys
import os


import socket
import time
import threading

HOST = '192.168.80.150'  # Replace with the microcontroller's IP address if needed
PORT = 80

def send_signal_data():
    """Sends signal data to the microcontroller via socket."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            while True:
                signal_status = ""
                for i in range(0, noOfSignals):
                    if i == currentGreen:
                        if currentYellow == 0:
                            signal_status += f"G{i+1}:{signals[i].green},"  # Green light status
                        else:
                            signal_status += f"Y{i+1}:{signals[i].yellow}," # Yellow light status
                    else:
                        signal_status += f"R{i+1}:{signals[i].red},"    # Red light status
                signal_status = signal_status[:-1] # Remove trailing comma
                s.sendall(signal_status.encode())
                time.sleep(1)  # Send data every second (adjust as needed)
        except ConnectionRefusedError:
            print("Microcontroller connection refused. Retrying...")
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            print(f"Socket error: {e}")
            time.sleep(5) #Wait before retrying.

# options={
#    'model':'./cfg/yolo.cfg',     #specifying the path of model
#    'load':'./bin/yolov2.weights',   #weights
#    'threshold':0.3     #minimum confidence factor to create a box, greater than 0.3 good
# }

# tfnet=TFNet(options)    #READ ABOUT TFNET

# Default values of signal times
defaultRed = 150
defaultYellow = 5
defaultGreen = 15
defaultMinimum = 10  # Set minimum green time to 10 seconds
defaultMaximum = 60

signals = []
noOfSignals = 4
simTime = 300       # change this to change time of simulation
timeElapsed = 0

currentGreen = 0   # Indicates which signal is green
nextGreen = (currentGreen+1)%noOfSignals
currentYellow = 0   # Indicates whether yellow signal is on or off 

# Average times for vehicles to pass the intersection
carTime = 2
bikeTime = 1
rickshawTime = 2.25 
busTime = 2.5
truckTime = 2.5

# Count of cars at a traffic signal
noOfCars = 0
noOfBikes = 0
noOfBuses =0
noOfTrucks = 0
noOfRickshaws = 0
noOfLanes = 2

# Red signal time at which cars will be detected at a signal
detectionTime = 1 ## update this value

speeds = {'car':0.5, 'bus':0.2, 'truck':0.2, 'rickshaw':0.4, 'bike':0.5}  # average speeds of vehicles

# Coordinates of start
x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}    
y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'rickshaw', 4:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}

# Coordinates of signal image, timer, and vehicle count
# signalCoods = [(530,230),(810,230),(810,570),(530,570)]
# signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]
signalCoods = [(465,230),(825,180),(895,600),(535,640)]
signalTimerCoods = [(466,205),(826,155),(896,575),(536,615)]
vehicleCountCoods = [(430,250),(880,210),(950,630),(500,670)]
vehicleCountTexts = ["0", "0", "0", "0"]

# Coordinates of stop lines
# stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
# defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
stopLines = {'right': 570, 'down': 325, 'left': 830, 'up': 585}
defaultStop = {'right': 560, 'down': 315, 'left': 840, 'up': 595}
stops = {'right': [580,580,580], 'down': [320,320,320], 'left': [810,810,810], 'up': [545,545,545]}

mid = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}
rotationAngle = 3

# Gap between vehicles
gap = 15    # stopping gap
gap2 = 15   # moving gap

pygame.init()
simulation = pygame.sprite.Group()

# Add this after the other global variables at the top
consecutiveTurns = {}  # Track consecutive turns for each lane
maxConsecutiveTurns = 2  # Maximum consecutive turns allowed for any lane
for i in range(noOfSignals):
    consecutiveTurns[i] = 0

# Add this after the consecutiveTurns initialization
waitingRounds = {}  # Track how many rounds each lane has been waiting
maxWaitingRounds = 5  # Maximum rounds a lane can wait before getting priority
for i in range(noOfSignals):
    waitingRounds[i] = 0

class TrafficSignal:
    def __init__(self, red, yellow, green, minimum, maximum):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.signalText = "30"
        self.totalGreenTime = 0
        
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        # self.stop = stops[direction][lane]
        self.index = len(vehicles[direction][lane]) - 1
        path = r'images/' + direction + r'/' + vehicleClass + r'.png'
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

    
        if(direction=='right'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):    # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().width - gap         # setting stop coordinate as: stop coordinate of next vehicle - width of next vehicle - gap
            else:
                self.stop = defaultStop[direction]
            # Set new starting and stopping coordinate
            temp = self.currentImage.get_rect().width + gap    
            x[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif(direction=='left'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].currentImage.get_rect().width + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] += temp
            stops[direction][lane] += temp
        elif(direction=='down'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().height - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif(direction=='up'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].currentImage.get_rect().height + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] += temp
            stops[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.currentImage, (self.x, self.y))

    def move(self):
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.currentImage.get_rect().width>stopLines[self.direction]):   # if the image has crossed stop line now
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.x+self.currentImage.get_rect().width<mid[self.direction]['x']):
                    if((self.x+self.currentImage.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.x += self.speed
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 2
                        self.y += 1.8
                        if(self.rotateAngle==90):
                            self.turned = 1
                            # path = "images/" + directionNumbers[((self.direction_number+1)%noOfSignals)] + "/" + self.vehicleClass + ".png"
                            # self.x = mid[self.direction]['x']
                            # self.y = mid[self.direction]['y']
                            # self.image = pygame.image.load(path)
                    else:
                        if(self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2)):
                            self.y += self.speed
            else: 
                if((self.x+self.currentImage.get_rect().width<=self.stop or self.crossed == 1 or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x += self.speed  # move the vehicle



        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.currentImage.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.y+self.currentImage.get_rect().height<mid[self.direction]['y']):
                    if((self.y+self.currentImage.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.y += self.speed
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 2.5
                        self.y += 2
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or self.y<(vehicles[self.direction][self.lane][self.index-1].y - gap2)):
                            self.x -= self.speed
            else: 
                if((self.y+self.currentImage.get_rect().height<=self.stop or self.crossed == 1 or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y += self.speed
            
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.x>mid[self.direction]['x']):
                    if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.x -= self.speed
                else: 
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 1.8
                        self.y -= 2.5
                        if(self.rotateAngle==90):
                            self.turned = 1
                            # path = "images/" + directionNumbers[((self.direction_number+1)%noOfSignals)] + "/" + self.vehicleClass + ".png"
                            # self.x = mid[self.direction]['x']
                            # self.y = mid[self.direction]['y']
                            # self.currentImage = pygame.image.load(path)
                    else:
                        if(self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or self.x>(vehicles[self.direction][self.lane][self.index-1].x + gap2)):
                            self.y -= self.speed
            else: 
                if((self.x>=self.stop or self.crossed == 1 or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x -= self.speed  # move the vehicle    
            # if((self.x>=self.stop or self.crossed == 1 or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2))):                
            #     self.x -= self.speed
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.y>mid[self.direction]['y']):
                    if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                        self.y -= self.speed
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 1
                        self.y -= 1
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x<(vehicles[self.direction][self.lane][self.index-1].x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width - gap2) or self.y>(vehicles[self.direction][self.lane][self.index-1].y + gap2)):
                            self.x += self.speed
            else: 
                if((self.y>=self.stop or self.crossed == 1 or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y -= self.speed

# Initialization of signals with default values
def initialize():
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts4)
    repeat()

# Set time according to formula
def setTime():
    global noOfCars, noOfBikes, noOfBuses, noOfTrucks, noOfRickshaws, noOfLanes
    global carTime, busTime, truckTime, rickshawTime, bikeTime
    
    # Get the next green signal index
    direction = directionNumbers[nextGreen]
    
    # Count vehicles for the next green signal lane
    noOfCars, noOfBuses, noOfTrucks, noOfRickshaws, noOfBikes = 0, 0, 0, 0, 0
    
    # Count bikes in lane 0
    for j in range(len(vehicles[direction][0])):
        vehicle = vehicles[direction][0][j]
        if vehicle.crossed == 0:
            noOfBikes += 1
    
    # Count other vehicles in lanes 1 and 2
    for i in range(1, 3):
        for j in range(len(vehicles[direction][i])):
            vehicle = vehicles[direction][i][j]
            if vehicle.crossed == 0:
                vclass = vehicle.vehicleClass
                if vclass == 'car':
                    noOfCars += 1
                elif vclass == 'bus':
                    noOfBuses += 1
                elif vclass == 'truck':
                    noOfTrucks += 1
                elif vclass == 'rickshaw':
                    noOfRickshaws += 1
    
    # Calculate green time based on vehicle weights
    total_vehicles = noOfCars + noOfBikes + noOfBuses + noOfTrucks + noOfRickshaws
    
    # Use weighted formula for vehicles
    greenTime = math.ceil(((noOfCars*carTime) + (noOfRickshaws*rickshawTime) + 
                         (noOfBuses*busTime) + (noOfTrucks*truckTime) + 
                         (noOfBikes*bikeTime)) / (noOfLanes+1))
    
    # Alternative calculation for higher green times with more vehicles
    if total_vehicles > 10:
        # Scaled green time based on vehicle count
        greenTime = max(greenTime, total_vehicles * 2)
    
    # Debug information
    print('-' * 50)
    print(f'Lane {nextGreen+1} ({direction}) vehicle counts:')
    print(f'Cars: {noOfCars}, Bikes: {noOfBikes}, Buses: {noOfBuses}, Trucks: {noOfTrucks}, Rickshaws: {noOfRickshaws}')
    print(f'Total vehicles: {total_vehicles}')
    
    # Apply minimum and maximum constraints
    if greenTime < defaultMinimum:
        greenTime = defaultMinimum
    elif greenTime > defaultMaximum:
        greenTime = defaultMaximum
    
    print(f'Calculated Green Time for Lane {nextGreen+1}: {greenTime} seconds')
    print('-' * 50)
    
    # Set the green time for the next signal that will turn green
    signals[nextGreen].green = greenTime

def count_vehicles():
    vehicle_counts = {}
    for direction in vehicles:
        vehicle_counts[direction] = sum(len(vehicles[direction][lane]) for lane in range(3))
    return vehicle_counts

def select_next_green(visited_lanes):
    global consecutiveTurns, waitingRounds
    
    # Count vehicles in each lane
    vehicle_counts = {}
    for direction in vehicles:
        # Only count non-crossed vehicles that are waiting
        waiting_count = 0
        for lane in range(3):
            for vehicle in vehicles[direction][lane]:
                if vehicle.crossed == 0:
                    waiting_count += 1
        vehicle_counts[direction] = waiting_count
    
    # Print the counts and waiting rounds for debugging
    print("Current vehicle counts:", vehicle_counts)
    print("Consecutive turns:", consecutiveTurns)
    print("Waiting rounds:", waitingRounds)
    
    # First check if any lane has been waiting too long (priority override)
    for i in range(noOfSignals):
        if waitingRounds[i] >= maxWaitingRounds and i != currentGreen:
            print(f"Lane {i+1} has been waiting for {waitingRounds[i]} rounds - giving priority!")
            return i
    
    # Find the lane with the most vehicles that hasn't reached max consecutive turns
    max_vehicles = -1
    next_green_index = None
    
    # Check if any lane has reached max consecutive turns
    max_turns_reached = False
    for i in range(noOfSignals):
        if consecutiveTurns[i] >= maxConsecutiveTurns:
            max_turns_reached = True
            break
    
    for direction, count in vehicle_counts.items():
        direction_index = list(directionNumbers.keys())[list(directionNumbers.values()).index(direction)]
        
        # If a lane has reached max turns, don't consider it unless all lanes have had their turns
        if max_turns_reached and consecutiveTurns[direction_index] >= maxConsecutiveTurns:
            continue
            
        if count > max_vehicles:
            max_vehicles = count
            next_green_index = direction_index
    
    # If no suitable lane with vehicles is found, use standard rotation
    if next_green_index is None:
        next_green_index = (currentGreen + 1) % noOfSignals
        
    print(f"Selected next green: Lane {next_green_index+1} with {max_vehicles} vehicles")
    return next_green_index

def repeat():
    global currentGreen, currentYellow, nextGreen, consecutiveTurns, waitingRounds
    visited_lanes = set()

    # Start the socket thread
    socket_thread = threading.Thread(target=send_signal_data, daemon=True)
    socket_thread.start()

    while True:
        while(signals[currentGreen].green > 0):   # while the timer of current green signal is not zero
            printStatus()
            updateValues()
            if(signals[(currentGreen+1) % noOfSignals].red == detectionTime):    # set time of next green signal 
                thread = threading.Thread(name="detection", target=setTime, args=())
                thread.daemon = True
                thread.start()
            time.sleep(1)
        currentYellow = 1   # set yellow signal on
        vehicleCountTexts[currentGreen] = "0"
        # reset stop coordinates of lanes and vehicles 
        for i in range(0, 3):
            stops[directionNumbers[currentGreen]][i] = defaultStop[directionNumbers[currentGreen]]
            for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen]]
        while(signals[currentGreen].yellow > 0):  # while the timer of current yellow signal is not zero
            printStatus()
            updateValues()
            time.sleep(1)
        currentYellow = 0   # set yellow signal off
        
        # Only reset yellow and red times, NOT green time
        signals[currentGreen].yellow = defaultYellow
        signals[currentGreen].red = defaultRed
        
        visited_lanes.add(currentGreen)
        if len(visited_lanes) == noOfSignals:
            visited_lanes.clear()
        
        # Increment waiting rounds for all lanes except the current green
        for i in range(noOfSignals):
            if i != currentGreen:
                waitingRounds[i] += 1
        
        nextGreen = select_next_green(visited_lanes)
        
        # Update consecutiveTurns counter
        if nextGreen == currentGreen:
            consecutiveTurns[nextGreen] += 1
        else:
            # Reset the counter for the previous green, increment for new green
            consecutiveTurns[currentGreen] = 0
            consecutiveTurns[nextGreen] = 1
            
        # Reset waiting rounds for the lane that's getting a green signal
        waitingRounds[nextGreen] = 0
            
        print(f"Lane {nextGreen+1} now has {consecutiveTurns[nextGreen]} consecutive turns")
        print(f"Updated waiting rounds: {waitingRounds}")
        
        # Check if we need a default green time (if not already set by setTime)
        if signals[nextGreen].green <= 0:
            signals[nextGreen].green = defaultGreen
            
        currentGreen = nextGreen # set next signal as green signal
        signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green    # set the red time of next to next signal as (yellow time + green time) of next signal

# Print the signal timers on cmd
def printStatus():                                                                                           
	for i in range(0, noOfSignals):
		if(i==currentGreen):
			if(currentYellow==0):
				print(" GREEN TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
			else:
				print("YELLOW TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
		else:
			print("   RED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
	print()

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
                signals[i].totalGreenTime+=1
            else:
                signals[i].yellow-=1
        else:
            signals[i].red-=1

def generateVehicles():
    while(True):
        vehicle_type = random.randint(0,4)
        if(vehicle_type==4):
            lane_number = 0
        else:
            lane_number = random.randint(0,1) + 1
        will_turn = 0
        if(lane_number==2):
            temp = random.randint(0,4)
            if(temp<=2):
                will_turn = 1
            elif(temp>2):
                will_turn = 0
        temp = random.randint(0,999)
        direction_number = 0
        # Adjusted probabilities to favor left lane (70% chance)
        a = [250, 500, 750, 1000]  # Values defining probability ranges
        if(temp < a[0]):  # 0-699: 70% chance for left
            direction_number = 2  # left lane (index 2 in directionNumbers)
        elif(temp < a[1]):  # 700-799: 10% chance for right
            direction_number = 0  # right lane (index 0 in directionNumbers)
        elif(temp < a[2]):  # 800-899: 10% chance for down
            direction_number = 1  # down lane (index 1 in directionNumbers)
        elif(temp < a[3]):  # 900-999: 10% chance for up
            direction_number = 3  # up lane (index 3 in directionNumbers)
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(0.75)

def simulationTime():
    global timeElapsed, simTime
    while(True):
        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed==simTime):
            totalVehicles = 0
            print('Lane-wise Vehicle Counts')
            for i in range(noOfSignals):
                print('Lane',i+1,':',vehicles[directionNumbers[i]]['crossed'])
                totalVehicles += vehicles[directionNumbers[i]]['crossed']
            print('Total vehicles passed: ',totalVehicles)
            print('Total time passed: ',timeElapsed)
            print('No. of vehicles passed per unit time: ',(float(totalVehicles)/float(timeElapsed)))
            os._exit(1)
    

# Function to render a status box with information
def render_status_box(screen, font, status_info, colors):
    # Left panel - Current signal status
    left_status_surface = pygame.Surface((320, 150))
    left_status_surface.set_alpha(220)  # Transparency (0-255)
    left_status_surface.fill((20, 20, 20))  # Dark grey background
    screen.blit(left_status_surface, (10, 10))
    
    # Left panel title
    title = font.render("Current Signal Status", True, colors['yellow'])
    screen.blit(title, (20, 15))
    
    # Draw separator line
    pygame.draw.line(screen, colors['yellow'], (20, 40), (310, 40), 2)
    
    y_offset = 45
    line_height = 25
    
    # Current signal status (first 4 items)
    for i, (text, color) in enumerate(status_info[:4]):
        text_surface = font.render(text, True, color)
        screen.blit(text_surface, (20, y_offset))
        y_offset += line_height
    
    # Right panel - Stats
    right_status_surface = pygame.Surface((320, 280))
    right_status_surface.set_alpha(220)  # Transparency (0-255)
    right_status_surface.fill((20, 20, 20))  # Dark grey background
    screen.blit(right_status_surface, (1070, 10))
    
    # Right panel title
    title = font.render("Traffic Management Stats", True, colors['yellow'])
    screen.blit(title, (1080, 15))
    
    # Draw separator line
    pygame.draw.line(screen, colors['yellow'], (1080, 40), (1370, 40), 2)
    
    y_offset = 45
    
    # Consecutive turns and waiting rounds info (remaining items)
    for text, color in status_info[4:]:
        text_surface = font.render(text, True, color)
        screen.blit(text_surface, (1080, y_offset))
        y_offset += line_height

class Main:
    thread4 = threading.Thread(name="simulationTime",target=simulationTime, args=()) 
    thread4.daemon = True
    thread4.start()

    thread2 = threading.Thread(name="initialization",target=initialize, args=())    # initialization
    thread2.daemon = True
    thread2.start()

    # Colours 
    black = (0, 0, 0)
    white = (255, 255, 255)
    green = (0, 200, 0)
    red = (200, 0, 0)
    yellow = (200, 200, 0)
    blue = (0, 0, 200)
    grey = (50, 50, 50)
    
    # Dictionary of colors for easy access
    colors = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'green': (0, 200, 0),
        'red': (200, 0, 0),
        'yellow': (200, 200, 0),
        'blue': (0, 0, 200),
        'grey': (50, 50, 50)
    }

    # Screensize 
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/intersection_resolution_set.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")

    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)
    statusFont = pygame.font.Font(None, 24)

    thread3 = threading.Thread(name="generateVehicles",target=generateVehicles, args=())    # Generating vehicles
    thread3.daemon = True
    thread3.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background,(0,0))   # display background in simulation
        
        # Prepare status information
        status_info = []
        
        # Current green light info
        current_direction = directionNumbers[currentGreen]
        if currentYellow == 0:
            status_info.append((f"Green: Lane {currentGreen+1} ({current_direction.upper()})", green))
            status_info.append((f"Time remaining: {signals[currentGreen].green} seconds", white))
        else:
            status_info.append((f"Yellow: Lane {currentGreen+1} ({current_direction.upper()})", yellow))
            status_info.append((f"Time remaining: {signals[currentGreen].yellow} seconds", white))
        
        # Display next lane info
        next_lane_text = f"Next: Lane {nextGreen+1} ({directionNumbers[nextGreen].upper()})"
        if nextGreen == currentGreen:
            next_lane_text += " (consecutive)"
        status_info.append((next_lane_text, blue))
        
        # Green time allocation info
        status_info.append((f"Allocated time: {signals[nextGreen].green} seconds", white))
        
        # Consecutive turns info
        status_info.append(("Consecutive turns:", white))
        for i in range(noOfSignals):
            color = red if consecutiveTurns[i] >= maxConsecutiveTurns else white
            status_info.append((f"  Lane {i+1}: {consecutiveTurns[i]}/{maxConsecutiveTurns}", color))
        
        # Waiting rounds info
        status_info.append(("Waiting rounds:", white))
        for i in range(noOfSignals):
            color = red if waitingRounds[i] >= maxWaitingRounds else white
            status_info.append((f"  Lane {i+1}: {waitingRounds[i]}/{maxWaitingRounds}", color))
        
        # Render the status box
        render_status_box(screen, statusFont, status_info, colors)
        
        for i in range(0,noOfSignals):  # display signal and set timer according to current status: green, yello, or red
            if(i==currentGreen):
                if(currentYellow==1):
                    if(signals[i].yellow==0):
                        signals[i].signalText = "STOP"
                    else:
                        signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    if(signals[i].green==0):
                        signals[i].signalText = "SLOW"
                    else:
                        signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if(signals[i].red<=10):
                    if(signals[i].red==0):
                        signals[i].signalText = "GO"
                    else:
                        signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["","","",""]

        # display signal timer and vehicle count
        for i in range(0,noOfSignals):  
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i],signalTimerCoods[i]) 
            displayText = vehicles[directionNumbers[i]]['crossed']
            vehicleCountTexts[i] = font.render(str(displayText), True, black, white)
            screen.blit(vehicleCountTexts[i],vehicleCountCoods[i])

        timeElapsedText = font.render(("Time Elapsed: "+str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText,(1100,600))

        # display the vehicles
        for vehicle in simulation:  
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            vehicle.move()
        pygame.display.update()

Main()


