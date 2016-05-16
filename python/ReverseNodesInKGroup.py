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
        
        if head is None or head.next is None:
            return head
        
        def reverseList(node):
            if node is None or node.next is None or k == 1:
                return node, node
            
            tmp = node.next
            nhead = ntail = node
            ntail.next = None
            
            while tmp is not None:
                next = tmp.next
                tmp.next = nhead
                nhead = tmp
                tmp = next
            
            return nhead, ntail
        
        
        i = 1
        tmp = head
        while i % k != 0 and tmp != None:
            tmp = tmp.next
            i += 1
            
        if tmp == None:
            # not enough 
            return head
        else:
            next = tmp.next
            tmp.next = None
            nh, nt = reverseList(head)
            rest = reverseList(next)[0]
            nt.next = rest
            return nh
        

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
    
    l = Solution().reverseKGroup(l, 2)
    
    tmp = l
    while tmp is not None:
        print(tmp.val)
        tmp = tmp.next
        