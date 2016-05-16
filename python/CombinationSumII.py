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
        
        def findSolution(candidates, target, idx, visited, sum, comb, allComb):
            if sum == target:
                allComb.append(comb[:])
                return
            
            for i in range(idx, len(candidates)):
                if visited[i]:
                    continue
                if (i == 0 or candidates[i] != candidates[i-1] or visited[i-1] == True) and candidates[i] + sum <= target:
                    visited[i] = True
                    comb.append(candidates[i])
                    findSolution(candidates, target, i + 1, visited, sum + candidates[i], comb, allComb)
                    comb.pop()
                    visited[i] = False
        
        comb = []
        allComb = []
        visited = [False] * len(candidates)
        sum = 0
        
        findSolution(candidates, target, 0, visited, sum, comb, allComb)
        
        return allComb

if __name__ == '__main__':
    s = Solution()
    #print(s.combinationSum2([23,32,22,19,29,15,11,26,28,20,34,5,34,7,28,33,30,30,16,33,8,15,28,26,17,10,25,12,6,17,30,16,6,10,23,22,20,29,14,5,6,5,5,6,29,20,34,24,16,7,22,11,17,7,33,21,13,15,29,6,19,16,10,21,21,28,8,6], 27))
    print(s.combinationSum2([8,7,4,3], 11))