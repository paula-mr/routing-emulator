import sys
import time
import os
import json
import socket
import getopt
import math
from datetime import datetime
from threading import Thread

def main(argv):
    print("Number of arguments:", len(argv), "arguments.")
    print("Argument List:", str(argv))

    address, pi_period, startup = get_startup_arguments(argv)

    neighbors = Neighbors()
    routing_table = RoutingTable(address)
    server = Server(address)
    server.create_socket()

    if startup:
        read_file(startup, server.address, neighbors, routing_table)

    try:
        update_routes = UpdateRoutesThread(pi_period, server, routing_table, server.address, neighbors)
        update_routes.start()

        remove_old_routes = RemoveOldRoutesThread(pi_period, routing_table, neighbors)
        remove_old_routes.start()

        listener = Listener(server, routing_table, neighbors)
        listener.start()

        listen_to_keyboard(neighbors, routing_table, server)
    except KeyboardInterrupt:
        os._exit(0)


def add_neighbor(ip, weight, current_address, neighbors, routing_table):
    if not is_ip_valid(ip):
        print(f"Ip {current_address} is invalid.")
        return

    neighbors.add(ip, weight)
    routing_table.add(ip, weight, current_address, ip)

def get_startup_arguments(argv):
    try:
        opts, args = getopt.getopt(argv,'a:u:s:',['addr=', 'update-period=', 'startup-commands='])
    except getopt.GetoptError:
        print("router.py <ADDR> <PERIOD> [STARTUP]")
        os._exit(1)

    address = None
    startup = None
    pi_period = None

    if opts:
        for opt, arg in opts:
            if opt in ('-a', '--addr'):
                address = arg
            elif opt in ('-u', '--update-period'):
                pi_period = arg
            elif opt in ('-s', '--startup-commands'):
                startup = arg
    elif len(args) >= 2:
        address = args[0]
        pi_period = args[1]
        if len(args) == 3:
            startup = args[2]

    if not is_ip_valid(address):
        print(f"Ip {address} is invalid.")
        os._exit(1)

    if pi_period:
        pi_period = float(pi_period)
    else:
        pi_period = 10
    
    return address, pi_period, startup

def read_file(file_name, address, neighbors, routing_table):
    with open(file_name, "r") as f:
        lines = f.readlines()
        for line in lines:
            command = line.replace('\n', '')
            commands = command.split(" ")
            if commands[0] != 'add':
                print("Invalid command was read in startup file:", commands[0])
            elif len(commands) != 3:
                print("Invalid format was read in startup file:", commands)
            elif not is_ip_valid(commands[1]):
                    print("Invalid IP address.")
            else:
                ip = commands[1]
                weight = int(commands[2])
                add_neighbor(ip, weight, address, neighbors, routing_table)


def is_ip_valid(address):
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False

def listen_to_keyboard(neighbors, routing_table, server):
    while True:
        command = input()
        command.strip()
        command = command.split(' ')
        if command[0] == "quit":
            os._exit(0)
        elif command[0] == "add":
            if len(command) != 3:
                print('Invalid arguments.')
            else: 
                ip = command[1]
                weight = int(command[2])
                add_neighbor(ip, weight, server.address, neighbors, routing_table)
        elif command[0] == "del":
            if len(command) != 2:
                print('Invalid arguments.')
            else:
                ip = command[1]
                neighbors.delete(ip)
                routing_table.delete(ip, neighbors.links)
                routing_table.delete_related_routes(ip, neighbors.links)
        elif command[0] == "trace":
            if len(command) != 2:
                print('Invalid arguments.')
            else:
                destination_ip = command[1]
                message = TraceMessage(server.address, destination_ip)
                print('sending trace message', message.serialize())
                next_hop = routing_table.get_next_hop(destination_ip)
                if next_hop:
                    server.send_message(next_hop, message.serialize())
        else:
            print(f"Unknown command {command[0]}")


class Listener(Thread):
    def __init__(self, server, routing_table, neighbors):
        Thread.__init__(self)
        self.server = server
        self.routing_table = routing_table
        self.neighbors = neighbors
    
    def run(self):
        while True:
            message, _ = self.server.receive_message()
            message_type = message.get('type', None)
            if message_type == "trace":
                trace_message, destination = self.routing_table.handle_trace(message)
                route_message(self.server, self.routing_table, destination, message, trace_message)
            if message_type == "update":
                self.routing_table.handle_update(message, self.neighbors.links)
            if message_type == "data":
                data_message, destination = self.routing_table.handle_data(message)
                route_message(self.server, self.routing_table, destination, message, data_message)
            if not message_type:
                print('Unknown message type')

def route_message(server, routing_table, destination, original_message, new_message):
    if destination:
        server.send_message(destination, json.dumps(new_message))
    elif original_message['destination'] != server.address:
        send_destination_not_found_message(server, routing_table, original_message)

def send_destination_not_found_message(server, routing_table, message):
    destination_not_found_message = DataMessage(server.address, message['source'])
    destination_not_found_message.payload = {'message': f"No route found for source {message['source']}"}
    next_hop = routing_table.get_next_hop(destination_not_found_message.destination)
    if next_hop:
        server.send_message(next_hop, destination_not_found_message.serialize())


class UpdateRoutesThread(Thread):
    def __init__(self, pi_period, server, routing_table, address, neighbors):
        Thread.__init__(self)
        self.pi_period = pi_period
        self.server = server
        self.routing_table = routing_table
        self.address = address
        self.neighbors = neighbors
    
    def run(self):
        while True:
            time.sleep(self.pi_period)
            send_update_messages(self.server, self.routing_table, self.address, self.neighbors)


class RemoveOldRoutesThread(Thread):
    def __init__(self, pi_period, routing_table, neighbors):
        Thread.__init__(self)
        self.pi_period = pi_period
        self.routing_table = routing_table
        self.neighbors = neighbors
    
    def run(self):
        while True:
            time.sleep(self.pi_period)
            for route in self.routing_table.list_all():
                now = datetime.now()
                diff_time = now - self.routing_table.get(route).last_updated_at
                if diff_time.seconds >= 4*self.pi_period:
                    print("DELETING", route)
                    self.neighbors.delete(route)
                    self.routing_table.delete(route, self.neighbors.links)
                    self.routing_table.delete_related_routes(route, self.neighbors.links)
                    


def send_update_messages(server, routing_table, current_ip, neighbors):
    messages = [
        create_update_message(routing_table, current_ip, neighbor[0])
        for neighbor in neighbors.links.items()
    ]
    for message in messages:
        server.send_message(message.destination, message.serialize())


def create_update_message(table, current_ip, destination_ip):
    message = UpdateMessage(current_ip, destination_ip)
    distances = table.generate_distances(destination_ip)
    distances[current_ip] = 0
    message.distances = distances
    return message

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
            # se este ip for o destino, printa a mensagem
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
            # considerando peso do enlace para cálculo do peso até o destino
            weight = weight + self.get_link_weight(neighbors, message['source'])
            if destination not in self.links[self.current_ip]:
                self.links[self.current_ip][destination] = RoutingInformation(weight, message['source'], message['source'])
            routing_info_to_destination = self.links[self.current_ip][destination]
            routing_info_to_destination.last_updated_at = now
            # Bellman-Ford
            current_optimal_weight = self.links[self.current_ip][destination].weight
            if (weight < current_optimal_weight):
                routing_info_to_destination.weight = weight
                routing_info_to_destination.next_hop = message['source']
                routing_info_to_destination.source_ip = message['source']

    def get_links_from_source(self, source_ip):
        links_from_source = [item for item in self.links[self.current_ip] if self.links[self.current_ip][item].source_ip == source_ip]
        return links_from_source.copy()

class Neighbors:
    def __init__(self):
        self.links = {}
    
    def add(self, ip, weight):
        self.links[ip] = weight
    
    def delete(self, ip):
        self.links.pop(ip, None)

    def get(self, ip):
        return self.links.get(ip, None)
    
    def list_all(self):
        return self.links
    
    def list_keys(self):
        return list(self.links.keys())
    
class Message:
    def __init__(self, m_type, source, destination):
        self.type = m_type
        self.source = source
        self.destination = destination
    
    def serialize(self):
        return json.dumps(self.__dict__)


class DataMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "data", source, destination)
        self.payload = None

    def print_payload(self):
        print(self.payload)


class TraceMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "trace", source, destination)
        self.hops = [source]


class UpdateMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "update", source, destination)
        self.distances = {}

class Server:
    def __init__(self, address):
        self.PORT = 55151
        self.sock = None
        self.address = address

    def create_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.address, self.PORT))
        return self.sock

    def send_message(self, address, message):
        self.sock.sendto(message.encode('utf-8'), (address, self.PORT))
    
    def receive_message(self):
        data, address = self.sock.recvfrom(1024)
        return json.loads(data.decode()), address
        

if __name__ == "__main__":
    main(sys.argv[1:])
