import sys
import sched, time

from neighbors import Neighbors
from routing_table import RoutingTable
from message import UpdateMessage
from server import Server


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

    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(pi_period, 1, send_update_messages, argument=(server, routing_table, address, neighbors))
    scheduler.run()
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


def send_update_messages(server, routing_table, current_ip, neighbors):
    print("SENDING UPDATE MESSAGES")
    messages = list(
        map(
            lambda ip_weight: create_update_message(
                routing_table, current_ip, ip_weight[0], ip_weight[1]
            ),
            neighbors.links.items(),
        )
    )

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
