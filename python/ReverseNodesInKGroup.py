'''
Created on 20150818

@author: Kenneth Tse

Given a linked list, reverse the nodes of a linked list k at a time and return its modified list.

If the number of nodes is not a multiple of k then left-out nodes in the end should remain as it is.

You may not alter the values in the nodes, only nodes itself may be changed.

Only constant memory is allowed.

For example,
Given this linked list: 1->2->3->4->5

For k = 2, you should return: 2->1->4->3->5

For k = 3, you should return: 3->2->1->4->5
'''
# Definition for singly-linked list.
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None

class Solution:
    # @param {ListNode} head
    # @param {integer} k
    # @return {ListNode}
    def reverseKGroup(self, head, k):
        if k < 2:
            return head
        
        first = ListNode(0)
        first.next = head
        
        # point before reverse
        p = first
        
        while p.next is not None and p.next.next is not None:
            prev = p.next
            cur = p.next
            i = 0
            while cur is not None and i < k -1:
                tmp = cur.next
                cur.next = prev
                prev = cur
                cur = tmp
                i += 1
            
            if i == k -1: # finish a group
                tmp = p.next
                p.next.next = cur
                p.next = prev
                p = tmp
            else:
                cur = prev.next
                prev.next = None
                while cur != p.next:
                    tmp = cur.next
                    cur.next = prev
                    prev = cur
                    cur = tmp
                break
        return first.next           
        
        
        
        

if __name__ == '__main__':
    def createList(l):
        first = None
        last = None
        for i in l:
            n = ListNode(i)
            if first is None:
                first = n
            if last is not None:
                last.next = n
            last = n
        return first
    
    l = createList([1,2,3,4,5])
    
    l = Solution().reverseKGroup(l, 4)
    
    tmp = l
    while tmp is not None:
        print(tmp.val)
        tmp = tmp.next
        