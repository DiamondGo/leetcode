'''
Created on 20160508

@author: Kenneth Tse

Given an array of integers, find out whether there are two distinct indices i and j in the array such that the difference between nums[i] and nums[j] is at most t and the difference between i and j is at most k.
'''

class Solution(object):
    def containsNearbyAlmostDuplicate(self, nums, k, t):
        """
        :type nums: List[int]
        :type k: int
        :type t: int
        :rtype: bool
        """
        if len(nums) < 2 or k < 1 or t < 0:
            return False
            
        candimap = {}
        i = 0
        for i in range(len(nums)):
            md = nums[i] // max(t, 1)
            for m in [md, md-1, md+1]:
                candilist = candimap.get(m)
                if candilist:
                    for idx in candilist:
                        if abs(idx - i) <= k and abs(nums[i] - nums[idx]) <= t:
                            return True
            candilist = candimap.setdefault(md, [])
            candilist.append(i)
            
        return False
        

if __name__ == '__main__':
    s = Solution()
    print(s.containsNearbyAlmostDuplicate([-3,3], 2, 4))