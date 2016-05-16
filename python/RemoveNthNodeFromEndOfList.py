'''
Created on 20160508

@author: Kenneth Tse

Given a linked list, remove the nth node from the end of list and return its head.

For example,

   Given linked list: 1->2->3->4->5, and n = 2.

   After removing the second node from the end, the linked list becomes 1->2->3->5.
Note:
Given n will always be valid.
Try to do this in one pass.
'''

# Definition for singly-linked list.
class ListNode(object):
    def __init__(self, x):
        self.val = x
        self.next = None

class Solution(object):
    def removeNthFromEnd(self, head, n):
        """
        :type head: ListNode
        :type n: int
        :rtype: ListNode
        """
        i = 0
        tail = head
        
        while i < n and tail != None:
            tail = tail.next
            i += 1
        
        #if tail == None: # there are n node exactly
        #    return head.next # remove 1st from beginning
        
        nNode = head
        nBefore = None
        
        while tail != None:
            tail = tail.next
            nNode = nNode.next
            if nBefore is None:
                nBefore = head
            else:
                nBefore = nBefore.next
        
        if nBefore is None:
            return nNode.next
        else:
            nBefore.next = nNode.next
            return head

if __name__ == '__main__':
    s = Solution()
    
    n1 = ListNode(1)
    n2 = ListNode(2)
    n3 = ListNode(3)
    
    n1.next = n2
    n2.next = n3
    
    s.removeNthFromEnd(n1, 1)