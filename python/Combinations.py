'''
Created on 20160502

@author: Kenneth Tse

Given two integers n and k, return all possible combinations of k numbers out of 1 ... n.

For example,
If n = 4 and k = 2, a solution is:

[
  [2,4],
  [3,4],
  [2,3],
  [1,2],
  [1,3],
  [1,4],
]

'''

class Solution(object):
    def combine(self, n, k):
        """
        :type n: int
        :type k: int
        :rtype: List[List[int]]
        """
        if k > n: return [[]]
        
        allc = []
        
        # l = 
        def search(i, k, comb, allcomb):
            if n - i < k or k < 0:
                return
            if k == 0:
                allcomb.append(comb)
                return
            # take this
            search(i+1, k -1, comb + [i+1], allcomb)
            # not take this
            search(i+1, k, comb, allcomb)
            
        search(0, k, [], allc)
        return allc

if __name__ == '__main__':
    s = Solution()
    print(s.combine(1,1))