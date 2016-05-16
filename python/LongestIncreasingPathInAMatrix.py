'''
Created on 20160505

@author: Kenneth Tse

Given an integer matrix, find the length of the longest increasing path.

From each cell, you can either move to four directions: left, right, up or down. You may NOT move diagonally or move outside of the boundary (i.e. wrap-around is not allowed).

Example 1:

nums = [
  [9,9,4],
  [6,6,8],
  [2,1,1]
]
Return 4
The longest increasing path is [1, 2, 6, 9].

Example 2:

nums = [
  [3,4,5],
  [3,2,6],
  [2,2,1]
]
Return 4
The longest increasing path is [3, 4, 5, 6]. Moving diagonally is not allowed.

'''

class Solution(object):
    def longestIncreasingPath(self, matrix):
        """
        :type matrix: List[List[int]]
        :rtype: int
        """
        m = len(matrix)
        if m == 0: return 0
        n = len(matrix[0])
        if n == 0: return 0
        
        dp = [[0] * n for i in range(m)]
        
        def dis(matrix, m, n, i, j):
            if dp[i][j] > 0:
                return dp[i][j]
            
            for  dx, dy in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
                nx, ny = i + dx, j + dy
                if 0 <= nx < m and 0 <= ny < n and matrix[nx][ny] > matrix[i][j]:
                    dp[i][j] = max(dp[i][j], dis(matrix, m, n, nx, ny))
            
            dp[i][j] += 1
            return dp[i][j]
        
        maxdis = 0
        for i in range(m):
            for j in range(n):
                maxdis = max(maxdis, dis(matrix, m, n, i, j))
        
        return maxdis
        
        
        

if __name__ == '__main__':
    s = Solution()
    print(s.longestIncreasingPath([[9,9,4],[6,6,8],[2,1,1]]))