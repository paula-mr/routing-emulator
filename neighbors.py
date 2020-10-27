class Neighbors:
    def __init__(self):
        self.links = {}
    
    def add(self, ip, weight, learned_from = None):
        self.links[ip] = weight
    
    def delete(self, ip):
        self.links.pop(ip, None)

    def get(self, ip):
        return self.links.get(ip, None)
    
    def list_all(self):
        return self.links
    
    def list_keys(self):
        return list(self.links.keys())
    