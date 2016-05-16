'''
Created on 20160502

@author: Kenneth Tse

Implement an iterator over a binary search tree (BST). Your iterator will be initialized with the root node of a BST.

Calling next() will return the next smallest number in the BST.

'''

# Definition for a  binary tree node
# class TreeNode(object):
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None

class BSTIterator(object):
    def __init__(self, root):
        """
        :type root: TreeNode
        """
        self.stack = []
        self.pushIntoStack(root)
    
    def pushIntoStack(self, node):
        while node:
            self.stack.append(node)
            node = node.left
        
        

    def hasNext(self):
        """
        :rtype: bool
        """
        return len(self.stack) > 0
        

    def next(self):
        """
        :rtype: int
        """
        node = self.stack.pop()
        self.pushIntoStack(node.right)
        return node.val
        

# Your BSTIterator will be called like this:
# i, v = BSTIterator(root), []
# while i.hasNext(): v.append(i.next())

if __name__ == '__main__':
    pass