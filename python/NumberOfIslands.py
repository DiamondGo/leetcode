'''
Created on 20160511

@author: Kenneth Tse

Given a 2d grid map of '1's (land) and '0's (water), count the number of islands. An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically. You may assume all four edges of the grid are all surrounded by water.

Example 1:

11110
11010
11000
00000
Answer: 1

Example 2:

11000
11000
00100
00011
Answer: 3
'''

class Solution(object):
    def numIslands(self, grid):
        """
        :type grid: List[List[str]]
        :rtype: int
        """
        
        m = len(grid)
        if m == 0:
            return 0
        n = len(grid[0])
        if n == 0:
            return 0
            
        grid = [[int(ch) for ch in row] for row in grid]
        
        countNew = 0
        dxy = [(0,-1),(-1,0),(1,0),(0,1)]
        for i in range(m):
            for j in range(n):
                if grid[i][j] == 1:
                    countNew += 1
                    stack = [(i,j)]
                    while len(stack) > 0:
                        x, y = stack.pop()
                        grid[x][y] = -1
                        for dx, dy in dxy:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < m and 0 <= ny < n:
                                if grid[nx][ny] == 1:
                                    stack.append((nx, ny))
        
        return countNew
                    

if __name__ == '__main__':
    s = Solution()
    
    print(s.numIslands(["1111111"]))