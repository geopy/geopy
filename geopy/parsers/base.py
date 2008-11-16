class Parser(object):
    def find(self, document):
        raise NotImplementedError
    
    def find_first(self, document):
        for location in self.find_iter(document):
            return location

    def find_all(self, document):
        return list(self.find(document))
