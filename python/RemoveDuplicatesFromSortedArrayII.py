'''
Created on 20160504

@author: Kenneth Tse

Follow up for "Remove Duplicates":
What if duplicates are allowed at most twice?

For example,
Given sorted array nums = [1,1,1,2,2,3],

Your function should return length = 5, with the first five elements of nums being 1, 1, 2, 2 and 3. It doesn't matter what you leave beyond the new length.

'''

class Solution(object):
    def removeDuplicates(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        idx = 0
        cur = 0
        last = 0
        for i in range(len(nums)):
            if i == 0 or nums[i] != nums[cur] or (nums[i] == nums[cur] and ((i == 1) or (i > 1 and nums[i] != last))):
                last = nums[cur]
                nums[idx] = nums[i]
                idx += 1
                cur = i
        return idx
        

if __name__ == '__main__':
    s = Solution()
    print(s.removeDuplicates([1,1,1,2,2,2,3,3]))