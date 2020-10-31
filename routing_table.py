from datetime import datetime
from functools import reduce


class RoutingInformation:
    def __init__(self, weight, source_ip, next_hop):
        self.weight = weight
        self.last_updated_at = datetime.now()
        self.source_ip = source_ip
        self.next_hop = next_hop


def passes_split_horizon(destination_ip, key_value):
    return key_value[0] != destination_ip and key_value[1].source_ip != destination_ip


class RoutingTable:
    def __init__(self):
        self.links = {}

    def add(self, ip, weight, source_ip, next_hop):
        self.links[ip] = RoutingInformation(weight, source_ip, next_hop)
    
    def list_all(self):
        return self.links.copy()

    def delete(self, ip):
        self.links.pop(ip, None)

    def split_horizon(self, destination_ip):
        return [item for item in self.links.items() if passes_split_horizon(destination_ip, item)]

    def generate_distances(self, neighbor_ip, neighbor_link_weight):
        def extract_info(accumulated_dic, table_row_info):
            accumulated_dic[table_row_info[0]] = (
                table_row_info[1].weight + neighbor_link_weight
            )
            return accumulated_dic
        return reduce(extract_info, self.split_horizon(neighbor_ip), {})
