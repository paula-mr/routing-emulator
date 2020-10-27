from datetime import datetime

class Topology:
    def __init__(self):
        self.links = {}
    
    def add(self, ip, weight):
        self.links[ip] = {'weight': weight, 'last_updated_at': datetime.now()}
    
    def delete(self, ip):
        self.links.pop(ip, None)

    def get(self, ip):
        return self.links.get(ip, None)
    
    def list_all(self):
        return self.links
    
    def list_keys(self):
        return list(self.links.keys())
    