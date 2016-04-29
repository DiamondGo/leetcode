'''
Created on 20150921

@author: Kenneth Tse

Given a binary tree, return the inorder traversal of its nodes' values.

For example:
Given binary tree {1,#,2,3},
   1
    \
     2
    /
   3
return [1,3,2].

Note: Recursive solution is trivial, could you do it iteratively?

confused what "{1,#,2,3}" means? > read more on how binary tree is serialized on OJ.

'''
from lib2to3.pytree import Node

# Definition for a binary tree node.
# class TreeNode(object):
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None

class Solution(object):
    def inorderTraversal(self, root):
        """
        :type root: TreeNode
        :rtype: List[int]
        """
        if root is None: return []
        stack = []
        output = []
        node = root
        while node is not None:
            stack.append(node)
            node = node.left
        while len(stack) > 0:
            node = stack.pop()
            output.append(node)
            if node.right is not None:
                node = node.right
                while node is not None:
                    stack.append(node)
                    node = node.left
        return output
        
        

if __name__ == '__main__':
    pass