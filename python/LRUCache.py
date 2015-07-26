class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = self.next = None
        
    def setNeighbour(self, prev, next):
        self.prev = prev
        self.next = next
 
class LRUCache:

       

    # @param capacity, an integer
    def __init__(self, capacity):
        self.size = 0
        self.cap = capacity
        self.next = self.prev = self
        self.items = {}
        
    def remove(self, node):
        node.next.prev = node.prev
        node.prev.next = node.next
        
    def add(self, node):
        self.prev.next = node
        node.prev = self.prev
        node.next = self
        self.prev = node
        
    def pop(self):
        node = self.next
        node.next.prev = self
        self.next = node.next
        return node

    # @return an integer
    def get(self, key):
        node = self.items.get(key)
        if node is None:
            return -1
        else:
            self.remove(node)
            self.add(node)
            return node.value
            
    def set(self, key, value):
        node = self.items.get(key)
        if node is not None:
            self.remove(node)
            self.add(node)
            node.value = value
        else:
            node = Node(key, value)
            self.add(node)
            self.size += 1
            self.items[key] = node
            if self.size > self.cap:
                rmnode = self.pop()
                self.size -= 1
                del self.items[rmnode.key]
    

if __name__ == "__main__":
    lc = LRUCache(1)
    lc.set(2, 1)
    print(lc.get(2))

    lc.set(3, 2)
    print(lc.get(2))

    print(lc.get(3))
    
    cmdlist = "set(1,1),set(2,2),set(3,3),set(4,4),get(4),get(3),get(2),get(1),set(5,5),get(1),get(2),get(3),get(4),get(5)"
    
    