import sys
from topology import Topology

def main():
    print('Number of arguments:', len(sys.argv), 'arguments.')
    print('Argument List:', str(sys.argv))
    topology = Topology()

if __name__ == "__main__":
    main()
    