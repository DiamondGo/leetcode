'''
Created on 20160428

@author: Kenneth Tse

Given a binary search tree, write a function kthSmallest to find the kth smallest element in it.

Note: 
You may assume k is always valid, 1 <= k <= BST's total elements.

Follow up:
What if the BST is modified (insert/delete operations) often and you need to find the kth smallest frequently? How would you optimize the kthSmallest routine?

'''

# Definition for a binary tree node.
# class TreeNode(object):
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None

class Solution(object):
    def kthSmallest(self, root, k):
        """
        :type root: TreeNode
        :type k: int
        :rtype: int
        """
        self.step = 0
        
        return self.inorderTravel(root, k)
    
    def inorderTravel(self, node, k):
        if node == None:
            return -1
        lret = self.inorderTravel(node.left, k)
        if lret != -1:
            return lret

        self.step += 1
        if self.step == k:
            return node.val

        rret = self.inorderTravel(node.right, k)
        if rret != -1:
            return rret
        
        return -1

        

if __name__ == '__main__':
    pass