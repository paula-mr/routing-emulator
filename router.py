import sys
import time

from datetime import datetime

from neighbors import Neighbors
from routing_table import RoutingTable
from message import UpdateMessage
from server import Server
from threading import Thread

def main():
    print("Number of arguments:", len(sys.argv), "arguments.")
    print("Argument List:", str(sys.argv))
    address = sys.argv[1]
    pi_period = float(sys.argv[2])
    if len(sys.argv) == 4:
        filepath = sys.argv[3]
        # todo: abrir e ler arquivo
    neighbors = Neighbors()
    routing_table = RoutingTable()
    server = Server(address)
    server.create_socket()

    update_routes = UpdateRoutesThread(pi_period, server, routing_table, address, neighbors)
    update_routes.start()

    remove_old_routes = RemoveOldRoutesThread(pi_period, routing_table)
    remove_old_routes.start()

    while True:
        command = input()
        if command == "quit":
            return
        elif command == "add":
            ip = input()
            weight = int(input())
            neighbors.add(ip, weight)
            routing_table.add(ip, weight, address, ip)
            return
        elif command == "del":
            ip = input()
            neighbors.delete(ip)
            routing_table.delete(ip)
            return
        elif command == "trace":
            destination_ip = input()
            return
        else:
            print("comando errado")
            return


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
    def __init__(self, pi_period, routing_table):
        Thread.__init__(self)
        self.pi_period = pi_period
        self.routing_table = routing_table
    
    def run(self):
        while True:
            time.sleep(self.pi_period)
            for route in self.routing_table.links:
                now = datetime.now()
                diff_time = now - self.routing_table(route).last_updated_at
                if diff_time.seconds >= 4*self.pi_period:
                    print("Deleting ", route)
                    self.routing_table.delete(route)
                    


def send_update_messages(server, routing_table, current_ip, neighbors):
    print("Send update messages")
    messages = [
        create_update_message(routing_table, current_ip, neighbor[0], neighbor[1])
        for neighbor in neighbors.links.items()
    ]
    for message in messages:
        server.send_message(message.destination, message.serialize())


def create_update_message(table, current_ip, destination_ip, destination_link_weight):
    message = UpdateMessage(current_ip, destination_ip)
    distances = table.generate_distances(destination_ip, destination_link_weight)
    distances[current_ip] = destination_link_weight
    message.distances = distances
    return message


if __name__ == "__main__":
    main()
