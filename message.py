class Message:
    def __init__(self, m_type, source, destination):
        self.type = m_type
        self.source = source
        self.destination = destination


class DataMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "data", source, destination)
        self.payload = None


class TraceMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "trace", source, destination)
        self.hops = []


class UpdateMessage(Message):
    def __init__(self, source, destination):
        Message.__init__(self, "update", source, destination)
        self.distances = {}