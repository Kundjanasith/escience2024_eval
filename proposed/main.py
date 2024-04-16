from utils.packet import Packet 
from utils.connection import Connection 
from utils.switch import Switch 
import os 
import networkx as nx 
import numpy as np 
import matplotlib.pyplot as plt 
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import pickle
import sys
import tensorflow as tf 
import time 

input_path = sys.argv[1]
output_path = input_path.split('/')[3].split('.pkl')[0]
print(output_path)
os.system('mkdir results/%s'%output_path)
os.system('mkdir results/%s/tmp_pk'%output_path)
os.system('mkdir results/%s/loss_pk'%output_path)
os.system('mkdir results/%s/rewards_pk'%output_path)
os.system('mkdir results/%s/models'%output_path)

class Network():
    def __init__(self):
        self.switches = {}
        self.connections = {}
        self.remainingStreams = []
        self.successTransfer = []
        self.graph = nx.MultiDiGraph()
        self.nodes = ['Hokkaido','Tohoku','Kanto','Chubu','Kansai','Chugoku','Shikoku','Kyushu','Okinawa']
        self.node_colors = ['#ff8a69', '#3f9293','#6d4838','#5442f5','#a16bbe','#bef781','#1c2f65','#f8d247','#3c8167']
        self.graph.add_nodes_from(self.nodes)
        self.edge_colors = []
        self.edges = []
        for n1 in range(len(self.nodes)):
            for n2 in range(len(self.nodes)):
                if self.nodes[n1] != self.nodes[n2]:
                    r = (n1, n2) if n1 < n2 else (n2, n1)
                    n1n2 = np.load('../metadata/npy_hops/FROM%dTO%d.npy'%(r[1],r[0]))
                    self.edges.append((self.nodes[n1],self.nodes[n2],len(n1n2)))
                    self.edge_colors.append(self.node_colors[n1])
        self.graph.add_edges_from(self.edges)
        self.pos = nx.circular_layout(self.graph)  # You can use other layouts as well
        

        
        # INIT  SWITCHES
        for n in range(len(self.nodes)):
            self.switches[n] = Switch(n, output_path)
        # INIT CONNECTIONS
        for s1 in self.switches.keys():
            for s2 in self.switches.keys():
                if s1 == s2: continue
                r = (s1, s2) if s1 < s2 else (s2, s1)
                n1n2 = np.load('../metadata/npy_hops/FROM%dTO%d.npy'%(r[1],r[0]))
                connection = Connection(self.switches[s1],self.switches[s2],len(n1n2))
                self.switches[s1].addConnection(connection)
                self.connections['%d-%d'%(self.switches[s1].name,self.switches[s2].name)] = connection
        # for s1 in self.switches.keys(): 
        #     print('IIN',self.switches[s1].name,self.switches[s1].inConnections.keys())
        #     print('OUT',self.switches[s1].name,self.switches[s1].outConnections.keys())


    def inPacket(self, packet, t):
        if len(self.switches[packet.src].queue) < self.switches[packet.src].MAXIMUM_QUEUE - 1:
            self.switches[packet.src].enQueue(packet,t)
        else:
            self.remainingStreams.append(packet)

    def calculate_bezier_curve_points(self, start, control, end, t):
        x = (1 - t)**2 * start[0] + 2 * (1 - t) * t * control[0] + t**2 * end[0]
        y = (1 - t)**2 * start[1] + 2 * (1 - t) * t * control[1] + t**2 * end[1]
        return x, y

    def readableNanoSeconds(self, t):
        m = int(t / (60 * pow(10,6)))
        s = t - (m * (60 * pow(10,6)))
        return '%d M %02.6f S'%(m,s/pow(10,6))

    def run(self, t, episode):
        # print('===============',self.readableNanoSeconds(t))
        for s in self.switches.keys():
            if len(self.switches[s].queue) == 0: continue
            # print('--------><')
            # print('%dBEFORE'%s)
            # for p in self.switches[s].queue:
            #     print('S',p)
            # print('TAKE ACTION..........')
            for p in self.switches[s].queue:
                self.switches[s].randomForward(p,t)
            # print('AFTER')
            # for p in self.switches[s].queue:
            #     print('S',p)

        # FREE CONNECTION
        for c in self.connections.keys():
            if self.connections[c].packet == None: continue
            if t/pow(10,6) >= self.connections[c].availableTime and t != 0 and self.connections[c].packet != None:
                if len(self.switches[self.connections[c].dst.name].queue) < self.switches[self.connections[c].dst.name].MAXIMUM_QUEUE:
                    self.connections[c].packet.current_location = self.connections[c].dst.name
                    self.connections[c].packet.timestamp['IN-%d'%self.connections[c].dst.name] = t/pow(10,6) 
                    if self.connections[c].packet.current_location == self.connections[c].packet.dst:
                        self.successTransfer.append(self.connections[c].packet)
                        with open('results/%s/tmp_pk/%d/P%d.pkl'%(output_path,episode,self.connections[c].packet.id), 'wb') as file:
                            pickle.dump(self.connections[c].packet, file)
                        # for ss in self.switches.keys():
                        #     with open('tmp_pk/S%d.pkl'%ss, 'wb') as file:
                        #         pickle.dump(self.switches[ss], file)
                        # for cc in self.connections.keys():
                        #     with open('tmp_pk/C%s.pkl'%cc, 'wb') as file:
                        #         pickle.dump(self.connections[cc], file)
                    else:
                        self.switches[self.connections[c].dst.name].enQueue(self.connections[c].packet,t/pow(10,6))
                    self.connections[c].packet = None
                # else:


        # ENQUEUE
        for p in self.remainingStreams:
            if len(self.switches[p.src].queue) < self.switches[p.src].MAXIMUM_QUEUE - 1:
                # print('y')
                self.switches[p.src].enQueue(p,t) #sim time
                self.remainingStreams.remove(p)

def simulation(episode):
    with open(input_path, 'rb') as file:
        packets = pickle.load(file)
    # packets = packets[:10]
    packets_src = np.zeros(9)
    packets_dst = np.zeros(9)
    for p in packets:
        packets_src[p.src] = packets_src[p.src] + 1
        packets_dst[p.dst] = packets_dst[p.dst] + 1
    print('Total packets: ',len(packets))
    network = Network()
    for p in packets:
        network.inPacket(p,0)
    
    # INIT MODEL
    for s in network.switches.keys():
        network.switches[s].init_model(episode)

    # packets_in_each_sw = np.zeros(9)
    # for s in network.switches.keys():
    #     packets_in_each_sw[s] = len(network.switches[s].queue)
    # print('In queue packets',packets_in_each_sw,sum(packets_in_each_sw))
    # print('Remaining packets',len(network.remainingStreams))
    # print('Success packets',len(network.successTransfer))
    # packets_in_each_conn = 0
    # for c in network.connections.keys():
    #     if network.connections[c].packet != None:
    #         packets_in_each_conn = packets_in_each_conn + 1
    # print('Connection packets',packets_in_each_conn,'/',len(network.connections.keys()))
    SIMULATION_TIME = 10 #minutes
    SIMULATION_TIME = SIMULATION_TIME * 60 * pow(10,6) #microseconds
    os.system('mkdir results/%s/tmp_pk/%d'%(output_path,episode))
    for sim_time in range(SIMULATION_TIME):
        s_tem = time.time()
        network.run(sim_time,episode)
        e_tem = time.time()
        print('===========',network.readableNanoSeconds(sim_time),e_tem-s_tem)
        packets_in_each_sw = np.zeros(9)
        for s in network.switches.keys():
            packets_in_each_sw[s] = len(network.switches[s].queue)
        print('In queue packets',packets_in_each_sw,sum(packets_in_each_sw))
        print('Remaining packets',len(network.remainingStreams))
        print('Success packets',len(network.successTransfer))
        packets_in_each_conn = 0
        for c in network.connections.keys():
            if network.connections[c].packet != None:
                packets_in_each_conn = packets_in_each_conn + 1
        print('Connection packets',packets_in_each_conn,'/',len(network.connections.keys()))
        if sum(packets_in_each_sw) + len(network.remainingStreams) + len(network.successTransfer) + packets_in_each_conn != len(packets):
            print('ERRROR')
            break
        if len(network.successTransfer) == len(packets): 
            print('SUCCESS')
            break
    # AFTER SIMULATION
    print('----------------------------------')
    for s in network.switches.keys():
        # print(s)
        # print(len(network.switches[s].rewards),len(network.switches[s].states))
        # print(np.array(network.switches[s].rewards).shape,np.array(network.switches[s].states).shape)
        os.system('mkdir results/%s/rewards_pk/%d'%(output_path,episode))
        with open('results/%s/rewards_pk/%d/S%d.pkl'%(output_path,episode,s), 'wb') as file:
            pickle.dump(network.switches[s].rewards, file)
        if len(network.switches[s].states) == 0:
            os.system('mkdir results/%s/loss_pk/%d'%(output_path,episode))
            with open('results/%s/loss_pk/%d/S%d.pkl'%(output_path,episode,s), 'wb') as file:
                pickle.dump(-99, file)
            # grads = tape.gradient(loss, network.switches[s].model.trainable_variables)
            # network.switches[s].optimizer.apply_gradients(zip(grads, network.switches[s].model.trainable_variables))
            network.switches[s].model.save_weights('results/%s/models/S%d_EP%d.weights.h5'%(output_path,network.switches[s].name,episode))
        else:
            returns = np.cumsum(network.switches[s].rewards[::-1])[::-1]
            advantages = returns - np.mean(returns)
            with tf.GradientTape() as tape:
                logits = network.switches[s].model(network.switches[s].states)
                action_masks = tf.one_hot(network.switches[s].actions, 8)
                log_probs = tf.reduce_sum(action_masks * tf.math.log(logits), axis=1)
                loss = tf.reduce_mean(log_probs * network.switches[s].delay)
            os.system('mkdir results/%s/loss_pk/%d'%(output_path,episode))
            with open('results/%s/loss_pk/%d/S%d.pkl'%(output_path,episode,s), 'wb') as file:
                pickle.dump(loss, file)
            grads = tape.gradient(loss, network.switches[s].model.trainable_variables)
            network.switches[s].optimizer.apply_gradients(zip(grads, network.switches[s].model.trainable_variables))
            network.switches[s].model.save_weights('results/%s/models/S%d_EP%d.weights.h5'%(output_path,network.switches[s].name,episode))


for i in range(100):
    simulation(i)