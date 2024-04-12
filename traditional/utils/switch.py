import random, sys
import numpy as np 
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam 
from tensorflow.keras.losses import SparseCategoricalCrossentropy

class Switch(): # ACTION DESTINATION STATE --> current packet size, remainin_time
    def __init__(self, name):
        self.name = name 
        self.queue = []
        self.MAXIMUM_QUEUE = 10
        self.timestamp = {} # key[IN/OUT-PACKETID] = time_step
        self.inConnections = {}
        self.outConnections = {}
        self.model = None 
        self.optimizer = Adam(learning_rate=0.001)
        self.loss_fn = SparseCategoricalCrossentropy()
        self.episode = None
        self.epsilon = 0.1
        self.rewards = []
        self.states = []
        self.actions = []

    def init_model(self, ep): # execute this method after add out connection
        self.episode = ep
        len_out_bound = len(self.outConnections.keys()) # availability of each connection
        # packet size 
        # packet src
        # packet dst 
        # packet deadine --> deadline / pow(10,4)
        # Time from start_time --> t_current - start_time
        # Time to deadline --> deadline - t_current 
        # self.model = Sequential([
        #     Dense(64, activation='relu', input_shape=(len_out_bound+6,)),
        #     Dense(32, activation='relu'),
        #     Dense(len_out_bound, activation='softmax') # out bound remove self.name
        # ])
        self.model = Sequential([
            Dense(23, activation='relu', input_shape=(len_out_bound+6,)),
            Dense(11, activation='relu'),
            Dense(len_out_bound, activation='softmax') # out bound remove self.name
        ])
        if ep != 0:
            self.model.load_weights('main01_rl_models/S%d_EP%d.weights.h5'%(self.name,ep-1))


    def addConnection(self, connection):
        # print(connection)
        if connection.src.name == self.name:
            self.outConnections[connection.dst.name] = connection
            connection.dst.inConnections[self.name] = connection
        elif connection.dst.name == self.name:
            self.inConnections[connection.src.name] = connection
            connection.src.outConnections[self.name] = connection
        else:
            print('[ERROR] adding connections',self.name,connection.src,connection.dst)

    def randomForward(self, packet, t): #MOCK FORWARD TO DST
        ## 01
        # forwardTo = packet.dst

        ## 02 
        x = list(range(9))
        xy = []
        for k in packet.timestamp.keys():
            if len(k.split('-')) == 2:
                xy.append(int(k.split('-')[1]))
        forwardTo = random.choice(x)
        if forwardTo in xy:
            return 
        
        # if self.outConnections[forwardTo].isAvailable(t):
        if self.outConnections[forwardTo].packet == None:
            self.timestamp['OUT-%d'%packet.id] = t/pow(10,6)
            packet.timestamp['IN-%d-%d'%(packet.current_location,forwardTo)] = t/pow(10,6)
            packet.current_location = '%d-%d'%(packet.current_location,forwardTo)
            self.outConnections[forwardTo].inPacket(packet,t)
            self.queue.remove(packet)
            self.rewards.append(packet.deadline/pow(10,4)-t)
        else:
            self.rewards.append(-1)
            
        
        # print('AFTER')
        # print(packet,forwardTo)
        # print(self.queue)
        # if self.outConnections[forwardTo].packet != None:
        #     print(self.outConnections[forwardTo].packet.id)
        # else:
        #     print(self.outConnections[forwardTo].packet)

    def enQueue(self, packet, t):
        if len(self.queue) >= self.MAXIMUM_QUEUE:
            # print('ENQUEUE-F',packet,len(self.queue),self.name)
            return False 
        else:
            # print('ENQUUE-T')
            packet.current_location = self.name 
            self.timestamp['IN-%d'%packet.id] = t # WAITING ERROR
            packet.timestamp['IN-%d'%self.name] = t # WAITING ERROR
            self.queue.append(packet)
            return True

    def __str__(self):
        res = 'Switch [%s] has %d packets \n'%(self.name,len(self.queue))
        for i in self.queue:
            res += i.__str__() + '\n'
        res = res[:-1]
        return res