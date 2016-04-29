'''
Created on 20160425

@author: Kenneth Tse

Given an array of n integers where n > 1, nums, return an array output such that output[i] is equal to the product of all the elements of nums except nums[i].

Solve it without division and in O(n).

For example, given [1,2,3,4], return [24,12,8,6].

Follow up:
Could you solve it with constant space complexity? (Note: The output array does not count as extra space for the purpose of space complexity analysis.)

'''
from operator import *
from functools import *

class Solution(object):
    def productExceptSelf(self, nums):
        """
        :type nums: List[int]
        :rtype: List[int]
        """
        la = [1] * len(nums)
        for i in range(1, len(nums)):
            la[i] = la[i -1] * nums[i-1]
        print(la)
        
        lb = [1] * len(nums)
        for j in range(len(nums) -2, -1, -1):
            lb[j] = lb[j +1] * nums[j+1]
        print(lb)
            
        lc = [la[i] * lb[i] for i in range(len(nums))]
        return lc
        
if __name__ == '__main__':
    s = Solution()
    print(s.productExceptSelf([1,2,3]))
