'''
Created on 201605011

@author: Kenneth Tse

Given a singly linked list, determine if it is a palindrome.

Follow up:
Could you do it in O(n) time and O(1) space?
'''

# Definition for singly-linked list.
class ListNode(object):
    def __init__(self, x):
        self.val = x
        self.next = None

class Solution(object):
    def isPalindrome(self, head):
        """
        :type head: ListNode
        :rtype: bool
        """
        if head is None or head.next is None:
            return True
        
        def reverse(node):
            if node is None or node.next is None:
                return node, node
            
            tmp = node.next
            nhead = ntail = node
            ntail.next = None
            
            while tmp != None:
                next = tmp.next
                tmp.next = nhead
                nhead = tmp
                tmp = next
            
            return nhead, ntail
        
        slow = fast = head
        lastslow = None
        while fast and fast.next:
            lastslow = slow
            slow = slow.next
            fast = fast.next.next
        
        if fast: # odd node, slow is just the mid
            jpoint = slow
            revpoint = slow.next
        else: # even node, slow is just the beginning of the right half, lastslow if the last node before slow
            jpoint = lastslow
            revpoint = slow
        
        jpoint.next = None
        
        nhead, ntail = reverse(revpoint)
        tmp = head
        ntmp = nhead
        palindrome = True
        while ntmp:
            if ntmp.val != tmp.val:
                palindrome = False
                break
            tmp, ntmp = tmp.next, ntmp.next
        
        
        
        return palindrome
            
        

if __name__ == '__main__':
    s = Solution()
    
    n1 = ListNode(1)
    n2 = ListNode(2)
    n3 = ListNode(2)
    n4 = ListNode(1)
    
    n1.next = n2
    n2.next = n3
    n3.next = n4
    
    print(s.isPalindrome(n1))