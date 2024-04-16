import random, sys
import numpy as np 
from tensorflow.keras.layers import Dense, Concatenate, Flatten, Input, concatenate
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.optimizers import Adam 
from tensorflow.keras.losses import SparseCategoricalCrossentropy
import sys
from tensorflow.keras.utils import plot_model
import pickle 
class Switch(): # ACTION DESTINATION STATE --> current packet size, remainin_time
    def __init__(self, name, output_path):
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
        self.states01 = []
        self.states02 = []
        self.states03 = []
        self.actions = []
        self.delay = []
        self.output_path = output_path

    def init_model(self, ep): # execute this method after add out connection
        self.episode = ep
        len_out_bound = len(self.outConnections.keys()) # availability of each connection
        #1 model size 
        #2 scale time
        ## t_current, t_start, t_deadline
        ## t_expected_transmision = t_start + t_deadline 
        ## t_current / t_expected_transmission
        model1 = Sequential()
        model1.add(Input((len_out_bound+2,)))
        model1.add(Dense(len_out_bound*5, activation='relu'))
        model1.add(Dense(len_out_bound*3, activation='relu'))
        model1.add(Dense(len_out_bound, activation='softmax', name='out1'))
        self.model = model1
        if ep != 0:
            self.model.load_weights('results/%s/models/S%d_EP%d.weights.h5'%(self.output_path,self.name,ep-1))
        if ep >= 2:
            loss_arr = []
            for i in range(ep):
                with open('results/%s/loss_pk/%d/S%d.pkl'%(self.output_path,i,self.name), 'rb') as file:
                    loss = pickle.load(file)
                if loss == -99:
                    continue
                loss_arr.append(loss)
            loss_arr = np.array(loss_arr)
            if len(loss_arr) == 0:
                self.model.load_weights('results/%s/models/S%d_EP%d.weights.h5'%(self.output_path,self.name,ep-1))
            else:
                idx = np.argmin(loss_arr)
                self.model.load_weights('results/%s/models/S%d_EP%d.weights.h5'%(self.output_path,self.name,idx))

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
        ## 04 
        forwardTo = []
        
        state1 = [] # availability
        state2 = [] # src, dst --> to category
        state3 = [] # timeFromstart, timeToExpect, size
        for c in self.outConnections.keys():
            if self.outConnections[c].packet == None: # available
                state1.append(0)
            else:
                state1.append(1)
        num_neightboring = len(state1)
        t_current = t 
        t_start = packet.timestamp['IN-%d'%packet.src]
        t_expected = t_start + packet.deadline/pow(10,4)
        state1.append(packet.size)
        state1.append(t_current/t_expected)
        # print(state1)
        input_state = np.array([state1])

        sw_paths = []
        for k in packet.timestamp.keys():
            if len(k.split('-')) == 2:
                sw_paths.append(int(k.split('-')[1]))

        # while True:
        x = list(range(9))
        x.remove(self.name) 
        self.states.append(input_state)
        
        if np.random.rand() < self.epsilon:
            for sw in sw_paths:
                if sw == self.name: 
                    continue
                x.remove(sw)
            action = random.choice(x)
        else:
            # print(self.model.input_shape,self.model.output_shape,input_state.shape)
            action_probs = self.model.predict(input_state,verbose=0)
            action = np.argmax(action_probs)
            action = x[action]
        forwardTo = action
        self.actions.append(forwardTo)


            # if self.outConnections[forwardTo].packet == None:
            #     self.rewards.append(packet.deadline/pow(10,4)-t)
            #     break
            # else:
            #     self.rewards.append(-1)
                
            # if self.outConnections[forwardTo].packet == None:
            #     

        # print(forwardTo)

        
        
        # if self.outConnections[forwardTo].isAvailable(t):
        if self.outConnections[forwardTo].packet == None:
            tem_dd = packet.deadline/pow(10,4)
            t_start = packet.timestamp['IN-%d'%packet.src]
            if int(forwardTo) in sw_paths: #not forward:
                # print(forwardTo,packet)
                # p = self.outConnections[forwardTo].calculate_transmission_time(packet.size)
                try:
                    self.rewards.append( (tem_dd) / abs((t_start+tem_dd)-(t/pow(10,6))) )
                except:
                    self.rewards.append( 1 )
                # SELF DELAY
                # self.delay.append(0.001)
            else:
                # forward
                self.timestamp['OUT-%d'%packet.id] = t/pow(10,6)
                packet.timestamp['IN-%d-%d'%(packet.current_location,forwardTo)] = t/pow(10,6)
                packet.current_location = '%d-%d'%(packet.current_location,forwardTo)
                self.outConnections[forwardTo].inPacket(packet,t)
                self.queue.remove(packet)
                t_start = packet.timestamp['IN-%d'%packet.src]
                t_current = t/pow(10,6)
                t_expected_arrive = t_start + packet.deadline/pow(10,4)
                t_willbe_arrive_at_dst = self.outConnections[forwardTo].availableTime
                if forwardTo == packet.dst:
                    # r = max((packet.deadline/pow(10,4))/abs(t_willbe_arrive_at_dst-t_start),1)
                    self.rewards.append( (tem_dd) / abs((t_start+tem_dd)-(t_willbe_arrive_at_dst)) )
                else:
                    # r = max((packet.deadline/pow(10,4))/abs(t_expected_arrive-t_current),1)
                    try:
                        self.rewards.append( (tem_dd) / abs((t_start+tem_dd)-(t/pow(10,6))) )
                    except:
                        self.rewards.append( 1 )
            # SELF DELAY
            d = packet.deadline/pow(10,4)
            t1 = packet.timestamp['IN-%d'%packet.src]
            t2 = self.outConnections[forwardTo].availableTime
            dd = (t2-t1)-d
            delay = dd
            self.delay.append(delay)                
        else: # penaly push to unavailable node
            # self.rewards.append(-1)
            # SELF DELAY (LOSS)
            # t2 = self.outConnections[forwardTo].availableTime
            self.delay.append(-1)

        

    def enQueue(self, packet, t):
        if len(self.queue) >= self.MAXIMUM_QUEUE:
            # print('ENQUEUE-F',packet,len(self.queue),self.name)
            return False 
        else:
            packet.current_location = self.name 
            self.timestamp['IN-%d'%packet.id] = t/pow(10,6) # WAITING ERROR
            packet.timestamp['IN-%d'%self.name] = t/pow(10,6) # WAITING ERROR
            self.queue.append(packet)
            return True

    def __str__(self):
        res = 'Switch [%s] has %d packets \n'%(self.name,len(self.queue))
        for i in self.queue:
            res += i.__str__() + '\n'
        res = res[:-1]
        return res