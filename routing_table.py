from datetime import datetime
from functools import reduce
import math

class RoutingInformation:
    def __init__(self, weight, next_hop, source_ip):
        self.weight = weight
        self.last_updated_at = datetime.now()
        self.next_hop = next_hop
        self.source_ip = source_ip


class RoutingTable:
    def __init__(self, current_ip):
        self.links = {}
        self.current_ip = current_ip
        self.links[current_ip] = {}
        self.links[current_ip][current_ip] = RoutingInformation(0, None, current_ip)

    def add(self, ip, weight, source_ip, next_hop):
        routingInformation = RoutingInformation(weight, next_hop, source_ip)
        if not self.links[source_ip]:
            self.links[source_ip] = { ip: routingInformation }
            for neighborTo in self.links.items():
                neighborTo[ip]: RoutingInformation(math.inf, None, source_ip)
        else:
            self.links[source_ip][ip] = routingInformation

    def get(self, ip):
        return self.links.get(self.current_ip, {}).get(ip, None)

    def list_all(self):
        neighbors = self.links[self.current_ip].copy()
        neighbors.pop(self.current_ip, None)
        return neighbors
    
    def list_dv(self):
        return self.links[self.current_ip].copy()

    def delete(self, ip):
        self.links[self.current_ip].pop(ip, None)
        self.links.pop(ip, None)

    @classmethod
    def passes_split_horizon(cls, destination_ip, route):
        return route[0] != destination_ip and route[1] != destination_ip

    def split_horizon(self, destination_ip):
        return [item for item in self.list_dv().items() if self.passes_split_horizon(destination_ip, item)]

    def generate_distances(self, neighbor_ip, neighbor_link_weight):
        def extract_info(accumulated_dic, table_row_info):
            accumulated_dic[table_row_info[0]] = (
                table_row_info[1].weight + neighbor_link_weight
            )
            return accumulated_dic
        return reduce(extract_info, self.split_horizon(neighbor_ip), {})
