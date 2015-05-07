'''
Given an array with n objects colored red, white or blue, sort them so that objects of the same color are adjacent, with the colors in the order red, white and blue.

Here, we will use the integers 0, 1, and 2 to represent the color red, white, and blue respectively.

Note:
You are not suppose to use the library's sort function for this problem.

click to show follow up.

Follow up:
A rather straight forward solution is a two-pass algorithm using counting sort.
First, iterate the array counting number of 0's, 1's, and 2's, then overwrite array with total number of 0's, then 1's and followed by 2's.

Could you come up with an one-pass algorithm using only constant space?
'''
class Solution:
    # @param {integer[]} nums
    # @return {void} Do not return anything, modify nums in-place instead.
    def sortColors(self, nums):
        cr = cw = cb = 0
        r = w = b = 0
        while b < len(nums):
            if nums[b] == 0:
                cr += 1
                nums[r] = 0
                if cw > 0:
                    nums[w] = 1
                if cb > 0:
                    nums[b] = 2
                r += 1
                w += 1
                b += 1
            elif nums[b] == 1:
                cw += 1
                nums[w] = 1
                if cb > 0:
                    nums[b] = 2
                w += 1
                b += 1
            elif nums[b] == 2:
                cb += 1
                b += 1 

if __name__ == '__main__':
    nums = [0]
    Solution().sortColors(nums)
    print(nums)