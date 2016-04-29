'''
Created on 20160429

@author: Kenneth Tse

Given an array where elements are sorted in ascending order, convert it to a height balanced BST.
'''

# Definition for a binary tree node.
class TreeNode(object):
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

class Solution(object):
    def sortedArrayToBST(self, nums):
        """
        :type nums: List[int]
        :rtype: TreeNode
        """
        """
        t = TreeNode()
        mid = len(nums) / 2
        t.val = nums[mid]
        t.left = self.buildBST(nums, 0, mid -1)
        t.right = self.buildBST(nums, mid +1, len(nums) -1)
        """
        t = self.buildBST(nums, 0, len(nums) -1)
        
        return t
    
    def buildBST(self, nums, start, end):
        if end < start:
            return None
        mid = (start + end) // 2
        t = TreeNode(nums[mid])
        t.left = self.buildBST(nums, start, mid -1)
        t.right = self.buildBST(nums, mid +1, end)
        
        return t
        
        

if __name__ == '__main__':
    s = Solution()
    t = s.sortedArrayToBST([1, 3])
    print(t)