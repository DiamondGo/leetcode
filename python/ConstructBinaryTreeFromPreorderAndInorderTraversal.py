'''
Created on 20150811

@author: Kenneth Tse

Given preorder and inorder traversal of a tree, construct the binary tree.

Note:
You may assume that duplicates do not exist in the tree.

'''

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

class Solution:
    # @param {integer[]} preorder
    # @param {integer[]} inorder
    # @return {TreeNode}
    def buildTree(self, preorder, inorder):
        return self.buildSubTree(preorder, inorder, 0, len(preorder) -1, 0, len(inorder) -1)
    
    def buildSubTree(self, preorder, inorder, prestart, preend, instart, inend):
        if prestart > preend or instart > inend:
            return None
        
        rootVal = preorder[prestart]
        p = TreeNode(rootVal)
        
        k = inorder.index(rootVal)
        
        p.left = self.buildSubTree(preorder, inorder, prestart + 1, prestart + (k - instart), instart, k -1)
        p.right = self.buildSubTree(preorder, inorder, prestart + (k - instart) +1, preend, k +1, inend)
        return p
        

if __name__ == '__main__':
    Solution().buildTree([-1], [-1])