'''
Created on 20160503

@author: Kenneth Tse

Write an efficient algorithm that searches for a value in an m x n matrix. This matrix has the following properties:

Integers in each row are sorted from left to right.
The first integer of each row is greater than the last integer of the previous row.
For example,

Consider the following matrix:

[
  [1,   3,  5,  7],
  [10, 11, 16, 20],
  [23, 30, 34, 50]
]
Given target = 3, return true.

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
        
        l,r = 0, m-1
        
        while r >= l:
            mid = (l + r)// 2
            if matrix[mid][0] == target:
                return True
            if matrix[mid][0] > target:
                r = mid -1
            else:
                if mid + 1 <= r and matrix[mid +1][0] <= target:
                    l = mid + 1
                else:
                    break
        
        l, r = 0, n -1
        while r >= l:
            k = (l + r) // 2
            if matrix[mid][k] == target:
                return True
            if matrix[mid][k] < target:
                l = k + 1
            else:
                r = k - 1
        
        return False
        """
        mid = (l + r) // 2
        while r > l:
            mid = (l + r)//2
            if matrix[mid][0] == target:
                return True
            if matrix[mid][0] > target:
                r = mid - 1
            else:
                l = mid
        
        l, r = 0, n -1
        while r >= l:
            k = (l + r) // 2
            if matrix[mid][k] == target:
                return True
            if matrix[mid][k] > target:
                r = k - 1
            else:
                l = k + 1
        return False
        """

if __name__ == '__main__':
    s = Solution()
    print(s.searchMatrix([[1,3,5,7],[10,11,16,20],[23,30,34,50]], 11))