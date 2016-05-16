'''
Created on 20160501

@author: Kenneth Tse

Merge two sorted linked lists and return it as a new list. The new list should be made by splicing together the nodes of the first two lists.

'''

# Definition for singly-linked list.
class ListNode(object):
    def __init__(self, x):
        self.val = x
        self.next = None

class Solution(object):
    def mergeTwoLists(self, l1, l2):
        """
        :type l1: ListNode
        :type l2: ListNode
        :rtype: ListNode
        """
        if l1 == None:
            if l2 == None:
                return None
            else:
                return l2
        else:
            if l2 == None:
                return l1
        
        h = None
        l = None
        while l1 is not None and l2 is not None:
            if l1.val < l2.val:
                tmp = l1
                l1 = l1.next
            else:
                tmp = l2
                l2 = l2.next
            if l == None:
                h = tmp
            else:
                l.next = tmp
            l = tmp
        
        if l1 is not None:
            l.next = l1
        if l2 is not None:
            l.next = l2
        
        return h
            

if __name__ == '__main__':
    s = Solution()
    t = s.mergeTwoLists(ListNode(1), ListNode(2))
    while t:
        print(t.val)
        t = t.next