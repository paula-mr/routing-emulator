class MessageHandler:
    def __init__(self):
        pass

    @staticmethod
    def handle_trace(message):
        pass

    @staticmethod
    def handle_update(message):
        pass

    @staticmethod
    def handle_data(message):
        pass

    @staticmethod
    def message_handler_dic(message_type):
        if message_type == "trace":
            return MessageHandler.handle_trace
        if message_type == "update":
            return MessageHandler.handle_update
        if message_type == "data":
            return MessageHandler.handle_data
