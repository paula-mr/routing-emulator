import sys
from neighbors import Neighbors
from routing_table import RoutingTable
from message import UpdateMessage


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


def create_update_message(table, source, destination_ip):
    message = UpdateMessage(source, destination_ip)
    message.distances = table.generate_distances(destination_ip)
    return message


if __name__ == "__main__":
    main()
