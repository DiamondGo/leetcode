'''
Created on 20160502

@author: Kenneth Tse

Write an efficient algorithm that searches for a value in an m x n matrix. This matrix has the following properties:

Integers in each row are sorted in ascending from left to right.
Integers in each column are sorted in ascending from top to bottom.
For example,

Consider the following matrix:

[
  [1,   4,  7, 11, 15],
  [2,   5,  8, 12, 19],
  [3,   6,  9, 16, 22],
  [10, 13, 14, 17, 24],
  [18, 21, 23, 26, 30]
]
Given target = 5, return true.

Given target = 20, return false.

'''

class Solution(object):
    def searchMatrix(self, matrix, target):
        """
        :type matrix: List[List[int]]
        :type target: int
        :rtype: bool
        """
        
        
        
        m = len(matrix)
        if m < 1: return False
        n = len(matrix[0])
        if n < 1: return False
        
        found = [[0] * n for i in range(m)]
        
        def search(mtx, i, j):
            if found[i][j] != 0: return found[i][j]
            if mtx[i][j] == target:
                found[i][j] = True
                return True
            if mtx[i][j] > target:
                found[i][j] = False
                return False
            
            # <
            if i < m-1:
                if j < n-1:
                    found[i][j] = search(mtx, i +1, j) or search(mtx, i, j+1)
                else:
                    found[i][j] = search(mtx, i +1, j)
            else:
                if j < n-1:
                    found[i][j] = search(mtx, i, j+1)
                else:
                    found[i][j] = False
                    
            return found[i][j]
        
        return search(matrix, 0, 0)

if __name__ == '__main__':
    s = Solution()
    s.searchMatrix([[1,1]], 2)