import pickle 
from prettytable import PrettyTable
import glob 
from termcolor import colored
from utils.packet import Packet 

t = PrettyTable(['EP','0', '1', '2', '3', '4', '5', '6'])
# t.add_row(['Alice', 24])
# t.add_row(['Bob', 19])
# print(t)


def check_every_packet_arrive_dst(packet_path,j):
    # print(pow(10,j))
    packets = []
    # print(packet_path)
    for i in glob.glob(packet_path):
        with open(i,'rb') as handle:
            packets.append(pickle.load(handle))
    # print(len(packets))
    results = 0
    for p in packets:
        src = p.src 
        dst = p.dst
        # print(p.timestamp)
        if 'IN-%d'%p.src in p.timestamp.keys() and 'IN-%d'%p.dst in p.timestamp.keys():
            results = results + 1 
    return results == len(packets) == pow(10,j)

def check_proposed(packet_path,j):
    # print(packet_path)
    res = 0
    for e in range(100):
        if check_every_packet_arrive_dst(packet_path+'/%d/*.pkl'%e,j):
            res = res + 1
    return res 
        

    # print(pow(10,j))
    # packets = []
    # for i in glob.glob(packet_path):
    #     with open(i,'rb') as handle:
    #         packets.append(pickle.load(handle))
    # # print(len(packets))
    # results = 0
    # for p in packets:
    #     src = p.src 
    #     dst = p.dst
    #     # print(p.timestamp)
    #     if 'IN-%d'%p.src in p.timestamp.keys() and 'IN-%d'%p.dst in p.timestamp.keys():
    #         results = results + 1 
    # return results == len(packets) == pow(10,j)


# TRADITIONAL
# print('TRADITIONAL')
# for i in range(10):
#     res = ['T%d'%i]
#     for j in range(7):
#         # num_pack = len(glob.glob('../traditional/results/%02d_packet%02d/tmp_pk/*.pkl'%(i,j)))
#         # if num_pack == pow(10,j):
#         #     res.append(colored('O', 'green'))
#         # else:
#         #     res.append(colored('X', 'red'))
#         ch = check_every_packet_arrive_dst('../traditional/results/%02d_packet%02d/tmp_pk/*.pkl'%(i,j),j)
#         if ch:
#             res.append(colored('O', 'green'))
#         else:
#             res.append(colored('X', 'red'))
        
#     t.add_row(res)
# print(t)

# PROPOSED 
# t = PrettyTable(['EP','0', '1', '2', '3', '4', '5', '6'])
import os 
print('PROPOSED')
for i in range(10):
    res = ['T%d'%i]
    for j in range(2,3):
        #if i in [9,2,1]: continue
        # num_pack = len(glob.glob('../traditional/results/%02d_packet%02d/tmp_pk/*.pkl'%(i,j)))
        # if num_pack == pow(10,j):
        #     res.append(colored('O', 'green'))
        # else:
        #     res.append(colored('X', 'red'))
        ch = check_proposed('results/%02d_packet%02d/tmp_pk/'%(i,j),j)
        print(i,j,ch)
        cmd = 'time python3 main.py ../benchmark01/packets/%02d_packet%02d.pkl %d'%(i,j,ch-1)
        print(cmd)
        os.system('screen -dmS %d %s'%(i,cmd))
        # if ch != 0:
        #     res.append(colored(ch, 'green'))
        # else:
        #     res.append(colored('X', 'red'))
    # t.add_row(res)
# print(t)
