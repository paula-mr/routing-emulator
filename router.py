import sys
from neighbors import Neighbors
from routing_table import RoutingTable


def main():
    print("Number of arguments:", len(sys.argv), "arguments.")
    print("Argument List:", str(sys.argv))
    neighbors = Neighbors()
    routing_table = RoutingTable()
    while True:
        command = input()
        if command == "quit":
            return
        elif command == "add":
            neighbor_ip = input()
            weight = int(input())
            return
        elif command == "del":
            neighbor_ip = input()
            return
        elif command == "trace":
            destination_ip = input()
            return
        else:
            print("comando errado")
            return


if __name__ == "__main__":
    main()
