'''
Created on 20150810

@author: Kenneth Tse

Given a singly linked list L: L0¡úL1¡ú¡­¡úLn-1¡úLn,
reorder it to: L0¡úLn¡úL1¡úLn-1¡úL2¡úLn-2¡ú¡­

You must do this in-place without altering the nodes' values.

For example,
Given {1,2,3,4}, reorder it to {1,4,2,3}.

'''

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, x):
#         self.val = x
#         self.next = None

class Solution:
    # @param {ListNode} head
    # @return {void} Do not return anything, modify head in-place instead.
    def reorderList(self, head):
        if head is None or head.next is None:
            return
        
        # fast and slow
        s = f = head
        while f.next is not None and f.next.next is not None:
            s = s.next
            f = f.next.next
        # s is middle
            
        # reverse last half
        f = s.next
        while f.next is not None:
            tmp = s.next
            s.next = f.next
            f.next = f.next.next
            s.next.next = tmp
            
        # recorder
        f = head
        while s != f and s.next is not None:
            tmp = f.next
            f.next = s.next
            s.next = s.next.next
            f.next.next = tmp
            f = f.next.next
        
        return

            

if __name__ == '__main__':
    pass