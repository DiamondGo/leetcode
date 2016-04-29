'''
Created on 20150824

@author: Kenneth Tse

Given a collection of candidate numbers (C) and a target number (T), find all unique combinations in C where the candidate numbers sums to T.

Each number in C may only be used once in the combination.

Note:
All numbers (including target) will be positive integers.
The solution set must not contain duplicate combinations.
For example, given candidate set 10,1,2,7,6,1,5 and target 8, 
A solution set is: 
[1, 7] 
[1, 2, 5] 
[2, 6] 
[1, 1, 6] 
'''

class Solution(object):
    def combinationSum2(self, candidates, target):
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
        self.findSol(candi[1:], sol, target - candi[0], solset)
        sol.pop()
        
        # without first
        self.findSol(candi[1:], sol, target, solset)

if __name__ == '__main__':
    s = Solution()
    print(s.combinationSum2([23,32,22,19,29,15,11,26,28,20,34,5,34,7,28,33,30,30,16,33,8,15,28,26,17,10,25,12,6,17,30,16,6,10,23,22,20,29,14,5,6,5,5,6,29,20,34,24,16,7,22,11,17,7,33,21,13,15,29,6,19,16,10,21,21,28,8,6], 27))