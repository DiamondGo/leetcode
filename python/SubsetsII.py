'''
Created on 20160506

@author: Kenneth Tse

Given a collection of integers that might contain duplicates, nums, return all possible subsets.

Note:
Elements in a subset must be in non-descending order.
The solution set must not contain duplicate subsets.
For example,
If nums = [1,2,2], a solution is:

[
  [2],
  [1],
  [1,2,2],
  [2,2],
  [1,2],
  []
]
'''

class Solution(object):
    def subsetsWithDup(self, nums):
        """
        :type nums: List[int]
        :rtype: List[List[int]]
        """
        nums.sort()
        
        def basicComb(num, count):
            return [[num] * i for i in range(count +1)]
            
        output = [[]]
        idx = 0
        while idx < len(nums):
            tmp = idx + 1
            while tmp < len(nums) and nums[tmp] == nums[idx]:
                tmp += 1
            comb = basicComb(nums[idx], tmp - idx)
            output = [l + r for l in output for r in comb]
        
        return output

if __name__ == '__main__':
    s = Solution()
    print(s.subsetsWithDup([0]))