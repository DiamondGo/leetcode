'''
Created on 20160427

@author: Kenneth Tse

Given a binary tree, return the preorder traversal of its nodes' values.

For example:
Given binary tree {1,#,2,3},
   1
    \
     2
    /
   3
return [1,2,3].

'''

# Definition for a binary tree node.
# class TreeNode(object):
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None

class Solution(object):
    def preorderTraversal(self, root):
        """
        :type root: TreeNode
        :rtype: List[int]
        """
        if root is None: return []
        stack = [root]
        output = []
        while len(stack) > 0:
            node = stack.pop()
            if node is None: continue
            output.append(node.val)
            stack.append(node.right)
            stack.append(node.left)
        return output


            
        
        

if __name__ == '__main__':
    pass