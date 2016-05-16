'''
Created on 20160501

@author: Kenneth Tse

Given a collection of distinct numbers, return all possible permutations.

For example,
[1,2,3] have the following permutations:
[1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], and [3,2,1].

'''

class Solution(object):
    def permute(self, nums):
        """
        :type nums: List[int]
        :rtype: List[List[int]]
        """
        if nums is None or len(nums) == 0: return []
        if len(nums) == 1: return [nums]
        
        lessret = self.permute(nums[1:])
        
        ret = []
        
        for comb in lessret:
            for i in range(len(nums)):
                #ret.append(comb[:].insert(i, nums[0]))
                l = comb[:]
                l.insert(i, nums[0])
                ret.append(l)

        
        return ret
        
        

if __name__ == '__main__':
    s = Solution()
    print(s.permute([1,2,3]))