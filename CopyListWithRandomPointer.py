"""
A linked list is given such that each node contains an additional random pointer which could point to any node in the list or null.

Return a deep copy of the list.
"""


# Definition for singly-linked list with a random pointer.
class RandomListNode(object):
    def __init__(self, x):
        self.label = x
        self.next = None
        self.random = None

class Solution(object):
    def copyRandomList(self, head):
        """
        :type head: RandomListNode
        :rtype: RandomListNode
        """

        # duplicate after

        if head is None:
            return head

        tmp = head
        while tmp:
            node = RandomListNode(tmp.label)
            tmp.next, node.next = node, tmp.next
            tmp = node.next

        tmp = head
        while tmp:
            if tmp.random:
                tmp.next.random = tmp.random.next
            tmp = tmp.next.next

        cphead = head.next
        last = head
        cplast = cphead
        tmp = cphead.next
        count = 0
        while tmp:
            if count % 2 == 0:
                last.next = tmp
            else:
                cplast.next = tmp
            tmp = tmp.next
            count +=1

        last.next = None

        return cphead
        """
        cphead = head.next
        last = None
        tmp = head
        while tmp:
            node = tmp.next
            if tmp.random is not None:
                node.random = tmp.random.next

            tmp.next = node.next
            if last is not None:
                last.next = node
            last = node

        return cphead
        """

if __name__ == '__main__':
    s = Solution()

    n1 = RandomListNode(-1)
    n2 = RandomListNode(1)
    n1.next = n2

    nl = s.copyRandomList(n1)

