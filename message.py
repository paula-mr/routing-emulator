import json

class Message:
    def __init__(self, m_type, source, destination):
        self.type = m_type
        self.source = source
        self.destination = destination
    
    def serialize(self):
        return json.dumps(self.__dict__)


class DataMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "data", source, destination)
        self.payload = None

    def print_payload(self):
        print(self.payload)


class TraceMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "trace", source, destination)
        self.hops = [source]


class UpdateMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "update", source, destination)
        self.distances = {}