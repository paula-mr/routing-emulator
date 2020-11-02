import sys
import time
import os
import json
import socket
import getopt

from datetime import datetime

from neighbors import Neighbors
from routing_table import RoutingTable
from message import UpdateMessage, TraceMessage, DataMessage
from server import Server
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


if __name__ == "__main__":
    main(sys.argv[1:])
