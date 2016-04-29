'''
Created on 20151003

@author: Kenneth Tse

Given an array nums, write a function to move all 0's to the end of it while maintaining the relative order of the non-zero elements.

For example, given nums = [0, 1, 0, 3, 12], after calling your function, nums should be [1, 3, 12, 0, 0].

Note:
You must do this in-place without making a copy of the array.
Minimize the total number of operations.

'''

class Solution(object):
    def moveZeroes(self, nums):
        """
        :type nums: List[int]
        :rtype: void Do not return anything, modify nums in-place instead.
        """
        # method one
        # nums.sort(key = lambda x : 1 if x > 0 else 0, reverse = True)
        
        # method two
        start_idx = 0
        while start_idx < len(nums):
            # find 0
            zero_found = -1
            for zero_idx in range(start_idx, len(nums)):
                if nums[zero_idx] == 0:
                    zero_found = zero_idx
                    break
            if zero_found == -1:
                break
            # found zero, then search for non-zero
            nonzero_found = -1
            nonzero_idx = zero_found + 1
            while nonzero_idx < len(nums):
                if nums[nonzero_idx] != 0:
                    nonzero_found = nonzero_idx
                    break
                nonzero_idx += 1
            if nonzero_found == -1:
                break
            # found non-zero
            nums[zero_found], nums[nonzero_found] = nums[nonzero_found], nums[zero_found]
            start_idx = zero_found +1
                
                    

if __name__ == '__main__':
    s = Solution()
    l = [0,1,0,3,12]
    s.moveZeroes(l)
    print(l)