'''
Reverse a singly linked list.
'''

# Definition for singly-linked list.
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None

'''
class Solution:
    # @param {ListNode} head
    # @param {integer} m
    # @param {integer} n
    # @return {ListNode}
    def reverseBetween(self, head, m, n):
        if m >= n:
            return head
        idx = 1
        preblock = pm = pn = None
        node = head
        while node is not None:
            if m -1 == idx:
                preblock = node
            if m == idx:
                pm = node
            if n == idx:
                pn = node
                break
            idx += 1
            node = node.next
        if pn is None:
            return head
        
        pstart = pm
        pm = pm.next
        tmphead = tmptail = None
        tail = pn.next
        while pm != tail:
            tmp = pm.next
            
            if tmptail is None:
                tmptail = pm
            pm.next = tmphead
            tmphead = pm

            pm = tmp
            
        tmptail.next = pstart
        pstart.next = tail
        
        if m == 1:
            head = tmphead
        else:
            preblock.next = tmphead
        
        return head
'''
class Solution:
    # @param {ListNode} head
    # @return {ListNode}
    def reverseList(self, head):
        if head is None or head.next is None:
            return head
        
        hnext = head.next
        tmpHead = tmpTail = None
        
        while hnext is not None:
            tmp = hnext.next
            hnext.next = tmpHead
            tmpHead = hnext
            if tmpTail is None:
                tmpTail = hnext
            hnext = tmp
        
        head.next = None
        tmpTail.next = head

        return tmpHead
            
        
        
        
            
            
            

if __name__ == '__main__':
    a = ListNode(1)
    b = ListNode(2)
    a.next = b
    
    o = Solution().reverseList(a)
    while o is not None:
        print(o.val)
        o = o.next