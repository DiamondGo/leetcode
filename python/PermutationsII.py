'''
Created on 20160511

@author: Kenneth Tse

Given a collection of numbers that might contain duplicates, return all possible unique permutations.

For example,
[1,1,2] have the following unique permutations:
[1,1,2], [1,2,1], and [2,1,1].
'''

class Solution(object):
    def permuteUnique(self, nums):
        """
        :type nums: List[int]
        :rtype: List[List[int]]
        """
        if len(nums) == 0:
            return []
        if len(nums) <= 1:
            if len(nums) == 0:
                return []
            else:
                return [nums]
        
        nums.sort()
        
        def findPermute(nums, used, comb, allcomb):
            if len(comb) == len(nums):
                allcomb.append(comb[:])
                return
            
            for i in range(len(nums)):
                if used[i]:
                    continue
                if i == 0 or nums[i-1] != nums[i] or nums[i-1] == True:
                    used[i] = True
                    comb.append(nums[i])
                    findPermute(nums, used, comb, allcomb)
                    comb.pop()
                    used[i] = False
        
        used = [False] * len(nums)
        comb = []
        allcomb = []
        findPermute(nums, used, comb, allcomb)
        
        return allcomb
        
        
        

if __name__ == '__main__':
    s = Solution()
    print(s.permuteUnique([1,1]))