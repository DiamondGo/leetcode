'''
Created on 20150824

@author: Kenneth Tse

Given a set of candidate numbers (C) and a target number (T), find all unique combinations in C where the candidate numbers sums to T.

The same repeated number may be chosen from C unlimited number of times.

Note:
All numbers (including target) will be positive integers.
The solution set must not contain duplicate combinations.
For example, given candidate set 2,3,6,7 and target 7, 
A solution set is: 
[7] 
[2, 2, 3] 

'''
class Solution(object):
    def combinationSum(self, candidates, target):
        """
        :type candidates: List[int]
        :type target: int
        :rtype: List[List[int]]
        """
        if candidates is None or len(candidates) == 0:
            return []
        
        candidates.sort()
        
        solset = []
        
        for i in range(len(candidates)):
            sol = [candidates[i]]
            sum = target - candidates[i]
            self.findSol(candidates[i:], sol, sum, solset)
        
        return solset

            
        
    def findSol(self, candi, sol, target, solset):
        if target == 0:
            solset.append(sol[:])
            return
        elif target < 0 or len(candi) == 0:
            return
        
        # with first
        sol.append(candi[0])
        self.findSol(candi, sol, target - candi[0], solset)
        sol.pop()
        
        # without first
        self.findSol(candi[1:], sol, target, solset)


if __name__ == '__main__':
    s = Solution()
    print(s.combinationSum([2,3,7], 7))