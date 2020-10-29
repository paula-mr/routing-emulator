import sys
from neighbors import Neighbors
from routing_table import RoutingTable
from message import UpdateMessage
from server import Server


def main():
    print("Number of arguments:", len(sys.argv), "arguments.")
    print("Argument List:", str(sys.argv))
    address = sys.argv[1]
    pi_period = sys.argv[2]
    if len(sys.argv) == 4:
        filepath = sys.argv[3]
        # todo: abrir e ler arquivo
    neighbors = Neighbors()
    routing_table = RoutingTable()
    server = Server(address)
    server.create_socket()
    while True:
        command = input()
        if command == "quit":
            return
        elif command == "add":
            ip = input()
            weight = int(input())
            neighbors.add(ip, weight)
            return
        elif command == "del":
            ip = input()
            neighbors.delete(ip)
            return
        elif command == "trace":
            destination_ip = input()
            return
        else:
            print("comando errado")
            return


def send_update_messages(routing_table, current_ip, neighbors):
    return [
        create_update_message(routing_table, current_ip, neighbor[0], neighbor[1])
        for neighbor in neighbors.links.items()
    ]


def create_update_message(table, current_ip, destination_ip, destination_link_weight):
    message = UpdateMessage(current_ip, destination_ip)
    distances = table.generate_distances(destination_ip, destination_link_weight)
    distances[current_ip] = destination_link_weight
    message.distances = distances
    return message


if __name__ == "__main__":
    main()
