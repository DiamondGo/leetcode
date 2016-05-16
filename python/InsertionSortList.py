'''
Created on 20160508

@author: Kenneth Tse

Sort a linked list using insertion sort.
'''

# Definition for singly-linked list.
class ListNode(object):
    def __init__(self, x):
        self.val = x
        self.next = None

class Solution(object):
    def insertionSortList(self, head):
        """
        :type head: ListNode
        :rtype: ListNode
        """
        if head is None or head.next is None:
            return head
            
        tmp = head.next
        
        nhead = ntail = head
        ntail.next = None
        
        while tmp:
            next = tmp.next
            last = None
            ntmp = nhead
            while ntmp is not None and ntmp.val < tmp.val:
                last = ntmp
                ntmp = ntmp.next
            if ntmp == None:
                last.next = tmp
                ntail = tmp
                ntail.next = None
            else:
                if last == None:
                    tmp.next = nhead
                    nhead = tmp
                else:
                    last.next = tmp
                    tmp.next = ntmp
            tmp = next
        
        ntail.next = None
        return nhead
            

if __name__ == '__main__':
    s = Solution()
    
    n1 =ListNode(3)
    n2 =ListNode(2)
    n3 =ListNode(4)
    #n4 =ListNode(4)
    
    n1.next = n2
    n2.next = n3
    #n3.next = n4

    h = s.insertionSortList(n1)
    