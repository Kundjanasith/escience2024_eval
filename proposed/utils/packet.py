class Packet():
    def __init__(self, src, dst, size, deadline):
        self.id = id(self)
        self.src = src 
        self.dst = dst 
        self.size = size
        self.current_location = src
        self.deadline = deadline
        # self.period = period
        self.timestamp = {} #key[IN/OUT-SWITCH NAME] = time_step
        self.paths = [self.src] # correct nodes in path

    def __str__(self):
        res = 'ID: %d || %s --> %s [%02d] : current_location = %s, deadline = %d'%(self.id,self.src,self.dst,self.size,self.current_location,self.deadline)
        res += ' ' + str(self.timestamp)
        return res

    def isArrived(self):
        return self.current_location == self.dst 