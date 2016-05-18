"""
Two elements of a binary search tree (BST) are swapped by mistake.

Recover the tree without changing its structure.
"""


# Definition for a binary tree node.
class TreeNode(object):
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

class Solution(object):
    def recoverTree(self, root):
        """
        :type root: TreeNode
        :rtype: void Do not return anything, modify root in-place instead.
        """
        if root is None:
            return
        first = second = None
        node = previous = None
        stack = []
        while root or len(stack) > 0:
            if root:
                stack.append(root)
                root = root.left
                continue
            previous = node
            node = stack.pop()

            if previous and previous.val > node.val:
                if first is None:
                    first = previous
                    second = node
                else:
                    second = node

            root = node.right
        if first is not None:
            first.val, second.val = second.val, first.val

if __name__ == '__main__':
    s = Solution()
    n1 = TreeNode(2)
    n2 = TreeNode(1)
    n1.right = n2

    print(s.recoverTree(n1))
