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
        # newest_min_value = min(
        #     map(
        #         lambda info: info.weight,
        #         filter(
        #             lambda dic_received_from_ip: dic_received_from_ip is not None, 
        #             map(
        #                 lambda dic: dic.get(ip, None), 
        #                 self.links.values()
        #             )
        #         )
        #     ),
        #     default=math.inf
        # )
        self.links[self.current_ip][ip].weight = math.inf

        newest_min_value = math.inf
        self.links.pop(ip, None)
        for neighbor_ip, inner_dic in self.links.items():
            if ip in inner_dic:
                if (inner_dic[ip].weight < newest_min_value):
                    source = neighbor_ip
                    newest_min_value = inner_dic[ip].weight
            else:
                continue

        if newest_min_value == math.inf:
            self.links[self.current_ip].pop(ip, None)
        else:
            self.links[self.current_ip][ip].weight = newest_min_value
            self.links[self.current_ip][ip].source_ip = source
            self.links[self.current_ip][ip].next_hop = source

    @classmethod
    def passes_split_horizon(cls, destination_ip, route):
        return route[0] != destination_ip and route[1].source_ip != destination_ip

    def split_horizon(self, destination_ip):
        return [item for item in self.list_dv().items() if self.passes_split_horizon(destination_ip, item)]

    def generate_distances(self, neighbor_ip, neighbor_link_weight):
        def extract_info(accumulated_dic, table_row_info):
            accumulated_dic[table_row_info[0]] = (
                table_row_info[1].weight + neighbor_link_weight
            )
            return accumulated_dic
        return reduce(extract_info, self.split_horizon(neighbor_ip), {})

    def handle_data(self, message):
        if message['destination'] == self.current_ip:
            # se current for destino, printa a mensagem
            print(message['payload'])
            return None, None
        else:
            # se não, redireciona para o destino
            return message, self.get_next_hop(message['destination'])

    def handle_trace(self, message):
        print('EXECUTANDO TRACE', message)
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

    def handle_update(self, message):
        now = datetime.now()
        #atualizar entradas da linha de messageSource no nosso dv
        messages_distances_dic = message['distances'].items()
        self.links[message['source']] = self.create_distances_info_dic(messages_distances_dic, message['source'])
        #para cada vizinho v de message.source:
        print('EXECUTANDO HANDLE UPADTE')
        for destination, weight in messages_distances_dic:
            if destination not in self.links[self.current_ip]:
                self.links[self.current_ip][destination] = RoutingInformation(weight, message['source'], message['source'])
            routing_info_to_destination = self.links[self.current_ip][destination]
            routing_info_to_destination.last_updated_at = now
            current_optimal_weight = self.links[self.current_ip][destination].weight
            # if not message['source'] in self.links[self.current_ip]:
                # weight_to_source = math.inf
            # else:
                # weight_to_source = self.links[self.current_ip][message['source']].weight
            # weight_via_source = weight_to_source + weight
            if (weight < current_optimal_weight):
                routing_info_to_destination.weight = weight
                routing_info_to_destination.next_hop = message['source']
                routing_info_to_destination.source_ip = message['source']
        self.p_links()

    def p_links(self):
        # for ip, neighbors in self.links.items():
            # print(f'rotas recebidas de {ip}:')
        neighbors = self.links[self.current_ip]
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
