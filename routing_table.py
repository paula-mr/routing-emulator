from datetime import datetime


class RoutingInformation:
    def __init__(self, weight, source_ip, next_hop):
        self.weight = weight
        self.last_updated_at = datetime.now()
        self.source_ip = source_ip
        self.next_hop = next_hop


class RoutingTable:
    def __init__(self):
        self.links = {}
    
    def add(self, ip, weight, source_ip, next_hop):
        self.links[ip] = RoutingInformation(weight, source_ip, next_hop)