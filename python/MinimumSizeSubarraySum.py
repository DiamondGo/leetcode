"""
Given an array of n positive integers and a positive integer s, find the minimal length of a subarray of which the sum ≥ s. If there isn't one, return 0 instead.

For example, given the array [2,3,1,2,4,3] and s = 7,
the subarray [4,3] has the minimal length under the problem constraint.
"""


class Solution(object):
    def minSubArrayLen(self, s, nums):
        """
        :type s: int
        :type nums: List[int]
        :rtype: int
        """

        if len(nums) < 1:
            return 0

        left = right = 0
        sum = nums[0]
        minl, minr = -1, len(nums)
        while True:
            while sum < s and right < len(nums) - 1:
                right += 1
                sum += nums[right]

            while sum >= s and left <= right and left < len(nums) - 1:
                if right - left < minr - minl:
                    minl, minr = left, right
                left += 1
                sum -= nums[left - 1]

            if right == len(nums) - 1:
                if left == 0:
                    return 0
                break

        return minr - minl + 1

if __name__ == '__main__':
    s = Solution()
    print(s.minSubArrayLen(3, [1, 1]))