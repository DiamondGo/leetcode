"""
Given a binary tree, find its maximum depth.

The maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.
"""

# Definition for a  binary tree node
# class TreeNode:
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None

"""
class Solution:
    # @param root, a tree node
    # @return an integer
    def maxDepth(self, root):
        return 0 if root == None else max(self.maxDepth(root.left), self.maxDepth(root.right)) + 1
"""
class Solution:
    # @param root, a tree node
    # @return an integer
    def maxDepth(self, root):
        if root == None:
            return 0
        maxDep = curDep = 0
        nodeStack = [(root, 1)]
        while len(nodeStack) > 0:
            curNode, curDep = nodeStack.pop()
            if curDep > maxDep:
                maxDep = curDep
            if curNode.right is not None:
                nodeStack.append((curNode.right, curDep + 1))
            if curNode.left is not None:
                nodeStack.append((curNode.left, curDep + 1))
        return maxDep
                
        
            
if __name__ == '__main__':
    pass