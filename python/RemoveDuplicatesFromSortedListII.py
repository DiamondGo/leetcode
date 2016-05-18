"""
Given a sorted linked list, delete all nodes that have duplicate numbers, leaving only distinct numbers from the original list.

For example,
Given 1->2->3->3->4->4->5, return 1->2->5.
Given 1->1->1->2->3, return 2->3.
"""


# Definition for singly-linked list.
class ListNode(object):
    def __init__(self, x):
        self.val = x
        self.next = None


class Solution(object):
    def deleteDuplicates(self, head):
        """
        :type head: ListNode
        :rtype: ListNode
        """

        def findDupSeq(node):  # return pre of first dup, last dup
            if node is None or node.next is None:
                return False, None, None

            last = None
            tmp = node
            next = node.next

            while next is not None and tmp.val != next.val:
                last = tmp
                tmp = next
                next = next.next

            while next is not None and next.next is not None and next.next.val == next.val:
                next = next.next

            if tmp.next is None:  # not found till end
                return False, None, None

            return True, last, next

        tmp = head
        pretmp = None
        while tmp is not None:
            found, pre, last = findDupSeq(head)
            if found:
                if pre == None:
                    tmp = last.next
                    if pretmp is None:
                        head = tmp
                    else:
                        pretmp.next = tmp
                else:
                    pre.next = last.next
                    tmp = pre.next
                    pretmp = pre
            else:
                break

        return head

if __name__ == "__main__":
    s = Solution()
    n1 = ListNode(1)
    n2 = ListNode(2)
    n3 = ListNode(3)
    n4 = ListNode(3)
    n1.next = n2
    n2.next = n3
    n3.next = n4
    print(s.deleteDuplicates(n1))
