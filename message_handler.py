from message import DataMessage
import json
from math import inf

class MessageHandler:
    def __init__(self):
        pass

    @staticmethod
    def handle_trace(message, current_ip):
        # sempre adicionar proprio ip à lista de hops do trace (message.hops)
        message.hops.append(current_ip)
        # verificar se é destino do trace
        if message.destination == current_ip:
            # se current for destino: enviar mensagem de data para a origem. Payload = json da propria msg de trace
            data_message = DataMessage(current_ip, message.source)
            data_message.payload = json.dumps(message.__dict__)
            return message, message.source
        else:
            return message, message.destination

    # @staticmethod
    def handle_update(self, message, current_ip):
        #todo transformar message.distances em dicionario de RoutingInformation
        self.links[message.source] = message.distances
        dist_to_source = self.links[current_ip][message.source].weight
        for destination, weight in message.distances.items():    
            #se nó x (current) recebeu de A:
            #para cada vizinho v de A:
            self.links[current_ip][destination] = min(
                self.links[current_ip].get(destination, inf), 
                dist_to_source + weight
            )


    @staticmethod
    def handle_data(message):
        print(message['payload'])

