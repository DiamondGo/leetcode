'''
Given n, how many structurally unique BST's (binary search trees) that store values 1...n?

For example,
Given n = 3, there are a total of 5 unique BST's.

   1         3     3      2      1
    \       /     /      / \      \
     3     2     1      1   3      2 
    /     /       \                 \
   2     1         2                 3
'''

"""
class Solution:
    # @return an integer
    numTreesResult = None
    def numTrees(self, n):
        if n == 0 or n == 1:
            return 1
        Solution.numTreesResult = [0] * (n + 1)
        Solution.numTreesResult[0] = 1
        Solution.numTreesResult[1] = 1
        return self.numTreesFact(n)
    
    def numTreesFact(self, n):
        if Solution.numTreesResult[n] == 0:
            Solution.numTreesResult[n] = sum([self.numTreesFact(i) * self.numTreesFact(n - 1 - i) for i in range(n)])
        return Solution.numTreesResult[n]
"""

class Solution:
    # @return an integer
    def numTrees(self, n):
        if n == 0 or n == 1:
            return 1
        numTreesResult = [1] * (n + 1)
        for i in range(2, n + 1):
            numTreesResult[i] = sum([ numTreesResult[k] * numTreesResult[i - 1 - k] for k in range(i)])
        return numTreesResult[n]
    

if __name__ == '__main__':
    s = Solution()
    print(s.numTrees(5))
