import math
import json

from datetime import datetime
from functools import reduce

from message import DataMessage

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
        self.links[self.current_ip][ip] = RoutingInformation(weight, next_hop, source_ip)

    def get(self, ip):
        return self.links.get(self.current_ip, {}).get(ip, None)

    def list_all(self):
        neighbors = self.links[self.current_ip].copy()
        neighbors.pop(self.current_ip, None)
        return neighbors

    def delete(self, ip, neighbors):
        self.links.pop(ip, None)
        self.links[self.current_ip][ip].weight = math.inf
        
        newest_min_value = math.inf
        for neighbor_ip, inner_dic in self.links.items():
            if ip in inner_dic:
                if (inner_dic[ip].weight < newest_min_value):
                    source = neighbor_ip
                    newest_min_value = inner_dic[ip].weight
            else:
                continue
        
        if ip in neighbors and neighbors[ip] < newest_min_value:
            self.links[self.current_ip][ip].weight = neighbors[ip]
            self.links[self.current_ip][ip].source_ip = self.current_ip
            self.links[self.current_ip][ip].next_hop = ip
        elif newest_min_value == math.inf:
            self.links[self.current_ip].pop(ip, None)
        else:
            self.links[self.current_ip][ip].weight = newest_min_value
            self.links[self.current_ip][ip].source_ip = source
            self.links[self.current_ip][ip].next_hop = source

    def split_horizon(self, destination_ip):
        return [item for item in self.list_dv().items() if self.passes_split_horizon(destination_ip, item)]

    def list_dv(self):
        return self.links[self.current_ip].copy()

    @classmethod
    def passes_split_horizon(cls, destination_ip, route):
        return route[0] != destination_ip and route[1].source_ip != destination_ip

    def generate_distances(self, neighbor_ip):
        dic = {}
        for table_row_info in self.split_horizon(neighbor_ip):
            dic[table_row_info[0]] = table_row_info[1].weight
        return dic

    def handle_data(self, message):
        if message['destination'] == self.current_ip:
            # se current for destino, printa a mensagem
            print(message['payload'])
            return None, None
        else:
            # se não, redireciona para o destino
            return message, self.get_next_hop(message['destination'])

    def handle_trace(self, message):
        # sempre adicionar proprio ip à lista de hops do trace (message.hops)
        message.get('hops', []).append(self.current_ip)
        # verificar se é destino do trace
        if message['destination'] == self.current_ip:
            # se current for destino: enviar mensagem de data para a origem. Payload = json da propria msg de trace
            data_message = DataMessage(self.current_ip, message['source'])
            data_message.payload = json.dumps(message)
            return data_message.__dict__, message['source']
        else:
            # se não, redireciona para o destino
            return message, self.get_next_hop(message['destination'])
    
    def get_next_hop(self, ip):
        route = self.links[self.current_ip].get(ip, None)
        if not route:
            return None
        else:
            return route.next_hop

    def get_link_weight(self, neighbors, source):
        return neighbors.get(source, math.inf)

    def delete_related_routes(self, source_ip, neighbors):
        for item in self.get_links_from_source(source_ip):
            print('DELETING ITEM', item)
            self.delete(item, neighbors)

    def handle_update(self, message, neighbors):
        now = datetime.now()
        print('EXECUTANDO HANDLE UPADTE', message)
        #atualizar entradas da linha de messageSource no nosso dv
        messages_distances_dic = message['distances'].items()

        for item in self.get_links_from_source(message['source']):
            if item not in message['distances']:
                self.links[message['source']].pop(item, None)
                self.delete(item, neighbors)
        
        for updated_ip, new_weight in messages_distances_dic:
            new_weight = new_weight + self.get_link_weight(neighbors, message['source'])
            if message['source'] not in self.links:
                self.links[message['source']] = {}
            if updated_ip not in self.links[message['source']]:
                self.links[message['source']][updated_ip] = RoutingInformation(new_weight, message['source'], message['source'])
            else:
                self.links[message['source']][updated_ip].weight = new_weight
                self.links[message['source']][updated_ip].last_updated_at = now
                self.links[message['source']][updated_ip].source_ip = message['source']

        #para cada vizinho v de message.source:
        for destination, weight in messages_distances_dic:
            weight = weight + self.get_link_weight(neighbors, message['source'])
            if destination not in self.links[self.current_ip]:
                self.links[self.current_ip][destination] = RoutingInformation(weight, message['source'], message['source'])
            routing_info_to_destination = self.links[self.current_ip][destination]
            routing_info_to_destination.last_updated_at = now
            current_optimal_weight = self.links[self.current_ip][destination].weight

            if (weight < current_optimal_weight):
                routing_info_to_destination.weight = weight
                routing_info_to_destination.next_hop = message['source']
                routing_info_to_destination.source_ip = message['source']
        
        self.p_links()

    def get_links_from_source(self, source_ip):
        links_from_source = [item for item in self.links[self.current_ip] if self.links[self.current_ip][item].source_ip == source_ip]
        print('LINKS FROM SOURCE', links_from_source)
        return links_from_source.copy()

    def p_links(self):
        for ip, neighbors in self.links.items():
            print(f'Rotas conhecidas de {ip}')
            for neighbor, route_info in neighbors.items():
                print(f'{neighbor}->{route_info.weight} source ip -> {route_info.source_ip}')

    def distance_tuple_to_routing_info(self, weight, source_ip):
        routing_info = RoutingInformation(weight, None, source_ip)
        return routing_info

    def create_distances_info_dic(self, distances, source_ip):
        dic = {}
        for (ip, weight) in distances:
            dic[ip] = self.distance_tuple_to_routing_info(weight, source_ip)
        return dic
