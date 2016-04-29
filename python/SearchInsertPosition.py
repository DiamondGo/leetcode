'''
Created on 20160429

@author: Kenneth Tse

Given a sorted array and a target value, return the index if the target is found. If not, return the index where it would be if it were inserted in order.

You may assume no duplicates in the array.

Here are few examples.
[1,3,5,6], 5 -> 2
[1,3,5,6], 2 -> 1
[1,3,5,6], 7 -> 4
[1,3,5,6], 0 -> 0

'''

class Solution(object):
    def searchInsert(self, nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: int
        """
        return self.searchInsertPart(nums, target, 0, len(nums) -1)
       
    def searchInsertPart(self, nums, target, start, end):
        pos = (start + end) // 2
        if nums[pos] == target:
            return pos
        elif nums[pos] > target:
            if pos == start:
                return pos
            else:
                return self.searchInsertPart(nums, target, start, pos)
        else: # < target
            if pos == end:
                return end +1
            else:
                return self.searchInsertPart(nums, target, pos, end)
            
        

if __name__ == '__main__':
    s = Solution()
    idx = s.searchInsert([1,3], 2)
    print(idx)