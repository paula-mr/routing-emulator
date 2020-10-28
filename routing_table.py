from datetime import datetime
from functools import reduce


class RoutingInformation:
    def __init__(self, weight, source_ip, next_hop):
        self.weight = weight
        self.last_updated_at = datetime.now()
        self.source_ip = source_ip
        self.next_hop = next_hop


def passes_split_horizon(destination_ip):
    def for_ip(k, v):
        return k != destination_ip and v.source_ip != destination_ip

    return for_ip


class RoutingTable:
    def __init__(self):
        self.links = {}

    def add(self, ip, weight, source_ip, next_hop):
        self.links[ip] = RoutingInformation(weight, source_ip, next_hop)

    def split_horizon(self, table, destination_ip):
        return filter(passes_split_horizon(destination_ip), table.items())

    def generate_distances(self, table, destination_ip):
        def extract_info(dic, table_row_info):
            dic[table_row_info.ip] = table_row_info.weight + self.links[destination_ip]

        return reduce(extract_info, self.split_horizon(table, destination_ip), {})
