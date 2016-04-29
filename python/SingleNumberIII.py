'''
Created on 20151014

@author: Kenneth Tse

Given an array of numbers nums, in which exactly two elements appear only once and all the other elements appear exactly twice. Find the two elements that appear only once.

For example:

Given nums = [1, 2, 1, 3, 2, 5], return [3, 5].

Note:
The order of the result is not important. So in the above example, [5, 3] is also correct.
Your algorithm should run in linear runtime complexity. Could you implement it using only constant space complexity?

'''
from functools import reduce

class Solution(object):
    def singleNumber(self, nums):
        """
        :type nums: List[int]
        :rtype: List[int]
        """
        f = lambda x,y : x^y
        
        cum = reduce(f, nums)
        
        bit = 0
        while (cum & 1) == 0:
            cum = cum >> 1
            bit += 1
        
        sign = 1 << bit
        
        a = reduce(f, [n for n in nums if n & sign == 0])
        b = reduce(f, [n for n in nums if n & sign != 0])
        return [a, b]
        

if __name__ == '__main__':
    pass