'''
Created on 20160507

@author: Kenneth Tse

Implement the following operations of a stack using queues.

push(x) -- Push element x onto stack.
pop() -- Removes the element on top of the stack.
top() -- Get the top element.
empty() -- Return whether the stack is empty.
Notes:
You must use only standard operations of a queue -- which means only push to back, peek/pop from front, size, and is empty operations are valid.
Depending on your language, queue may not be supported natively. You may simulate a queue by using a list or deque (double-ended queue), as long as you use only standard operations of a queue.
You may assume that all operations are valid (for example, no pop or top operations will be called on an empty stack).

'''

from collections import deque
class Stack(object):
    def __init__(self):
        """
        initialize your data structure here.
        """
        self.q = deque()
        self.tmpq = deque()
        self.cache = None
        

    def push(self, x):
        """
        :type x: int
        :rtype: nothing
        """
        if self.cache != None:
            self.q.append(self.cache)
        
        self.cache = x
        
        

    def pop(self):
        """
        :rtype: nothing
        """
        if self.cache != None:
            tmp = self.cache
            self.cache = None
            return tmp
        
        while len(self.q) > 0:
            item = self.q.popleft()
            if len(self.q) > 0:
                self.tmpq.append(item)
            else:
                self.q, self.tmpq = self.tmpq, self.q
                return item
        

    def top(self):
        """
        :rtype: int
        """
        if self.cache != None:
            return self.cache
        
        while len(self.q) > 0:
            item = self.q.popleft()
            if len(self.q) > 0:
                self.tmpq.append(item)
            else:
                self.cache = item
                self.q, self.tmpq = self.tmpq, self.q
                return self.cache
        
        

    def empty(self):
        """
        :rtype: bool
        """
        return len(self.q) == 0 and self.cache == None

if __name__ == '__main__':
    s = Stack()
    s.push(1)
    s.push(2)
    s.top()
    s.push(3)
    #s.pop()
    print(s.top())