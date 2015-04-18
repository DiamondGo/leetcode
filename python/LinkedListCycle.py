'''
Given a linked list, determine if it has a cycle in it.

Follow up:
Can you solve it without using extra space?
'''
from tkinter.tix import ListNoteBook

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, x):
#         self.val = x
#         self.next = None

class Solution:
    # @param head, a ListNode
    # @return a boolean
    def hasCycle(self, head):
        pass
            

        
        

if __name__ == '__main__':
    class ListNode:
         def __init__(self, x):
             self.val = x
             self.next = None
             
    l1 = ListNode(1)
    l2 = ListNode(2)
    l3 = ListNode(3)
    l4 = ListNode(4)
    
    l1.next = l1
    l2.next = l3
    l3.next = l4
    #l4.next = l4
    
    print(Solution().hasCycle(l1))
    