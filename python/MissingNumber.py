'''
Created on 20160426

@author: Kenneth Tse

Given an array containing n distinct numbers taken from 0, 1, 2, ..., n, find the one that is missing from the array.

For example,
Given nums = [0, 1, 3] return 2.

Note:
Your algorithm should run in linear runtime complexity. Could you implement it using only constant extra space complexity?

'''

from functools import reduce
from itertools import chain

class Solution(object):
    def missingNumber(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        
        f = lambda x,y : x ^ y
        return reduce(f, chain(nums, range(len(nums) +1)))


if __name__ == '__main__':
    pass