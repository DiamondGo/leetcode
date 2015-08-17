'''
Created on 20150817

@author: Kenneth Tse

Given an array of non-negative integers, you are initially positioned at the first index of the array.

Each element in the array represents your maximum jump length at that position.

Determine if you are able to reach the last index.

For example:
A = [2,3,1,1,4], return true.

A = [3,2,1,0,4], return false.
'''
class Solution:
    # @param {integer[]} nums
    # @return {boolean}
    def canJump(self, nums):
        #if len(nums) == 0 or nums[0] == 0:
        #    return False
        jumpLeft = nums[0]
        if jumpLeft == 0 and len(nums) > 1:
            return False
        
        for i in range(1, len(nums)):
            jumpLeft = max(jumpLeft -1, nums[i])
            if jumpLeft == 0:
                return False
        
        return True
        

if __name__ == '__main__':
    pass