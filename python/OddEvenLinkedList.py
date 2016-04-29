'''
Created on 20160428

@author: Kenneth Tse

Given a singly linked list, group all odd nodes together followed by the even nodes. Please note here we are talking about the node number and not the value in the nodes.

You should try to do it in place. The program should run in O(1) space complexity and O(nodes) time complexity.

Example:
Given 1->2->3->4->5->NULL,
return 1->3->5->2->4->NULL.

Note:
The relative order inside both the even and odd groups should remain as it was in the input. 
The first node is considered odd, the second node even and so on ...

'''

# Definition for singly-linked list.
# class ListNode(object):
#     def __init__(self, x):
#         self.val = x
#         self.next = None

class Solution(object):
    def oddEvenList(self, head):
        """
        :type head: ListNode
        :rtype: ListNode
        """
        if head is None or head.next is None:
            return head
        
        
        evenHead = evenTail = head
        oddHead = oddTail = head.next
        
        tmpOdd = oddHead.next
        index = 2
        

        while tmpOdd != None:
            if index % 2 == 0:
                evenTail.next = tmpOdd
                evenTail = tmpOdd
            else:
                oddTail.next = tmpOdd
                oddTail= tmpOdd
            tmpOdd = tmpOdd.next
            index += 1
            
        evenTail.next = oddHead
        oddTail.next = None
        
        return evenHead
            
        

            

        
        
        

if __name__ == '__main__':
    pass