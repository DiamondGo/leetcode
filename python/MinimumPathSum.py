'''
Created on 20160501

@author: Kenneth Tse

Given a m x n grid filled with non-negative numbers, find a path from top left to bottom right which minimizes the sum of all numbers along its path.

'''

class Solution(object):
    def minPathSum(self, grid):
        """
        :type grid: List[List[int]]
        :rtype: int
        """
        if grid is None: return 0
        
        m = len(grid)
        n = len(grid[0])
        dp = [[0] * n for i in range(m)]
        dp[m-1][n-1] = grid[m-1][n-1]
        
        def minPath(i, j):
            if dp[i][j] != 0:
                return dp[i][j]
            elif i == m -1:
                dp[i][j] = grid[i][j] + minPath(i, j+1)
            elif j == n -1:
                dp[i][j] = grid[i][j] + minPath(i+1, j)
            else:
                dp[i][j] = grid[i][j] + min(minPath(i, j+1), minPath(i+1, j))
            return dp[i][j]
        
        return minPath(0, 0)
                
        

if __name__ == '__main__':
    s = Solution()
    print(s.minPathSum([[0]]))