from message import DataMessage
import json


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

    @staticmethod
    def handle_update(message):
        pass

    @staticmethod
    def handle_data(message):
        print(message.payload)

    @staticmethod
    def message_handler_dic(message_type):
        if message_type == "trace":
            return MessageHandler.handle_trace
        if message_type == "update":
            return MessageHandler.handle_update
        if message_type == "data":
            return MessageHandler.handle_data
