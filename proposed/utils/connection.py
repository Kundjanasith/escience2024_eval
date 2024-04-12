class Connection():
    def __init__(self, src, dst, num_hops):
        self.src = src
        self.dst = dst 
        self.transmission_rate_gbps = 100 # GBPS
        self.availableTime = 0
        self.num_hops = num_hops
        self.packet = None

    def __str__(self):
        if self.packet != None:
            res = '%s-->%s : [PACKET %d] Available Time %f'%(self.src.name, self.dst.name, self.packet.id, self.availableTime)
        else:
            res = '%s-->%s : isAvialable'%(self.src.name, self.dst.name)
        return res

    def inPacket(self, packet, t):
        self.packet = packet 
        self.availableTime = t/pow(10,6) + self.calculate_transmission_time(packet.size)

    def calculate_transmission_time(self, data_size_megabytes):
        data_size_bits = data_size_megabytes * 8 * 10**6 #MB
        # data_size_bits = data_size_megabytes * 8 * 10**3 #KB
        transmission_rate_bps = self.transmission_rate_gbps * 10**9
        self.num_hops = 1 if self.num_hops == 0 else self.num_hops
        adjusted_transmission_rate_bps = transmission_rate_bps / self.num_hops
        time_seconds = data_size_bits / adjusted_transmission_rate_bps
        return time_seconds

    def isAvailable(self, t):
        if self.packet != None:
            return False 
        else:
            return True