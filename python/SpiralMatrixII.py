'''
Created on 20160501

@author: Kenneth Tse

Given an integer n, generate a square matrix filled with elements from 1 to n2 in spiral order.

For example,
Given n = 3,

You should return the following matrix:
[
 [ 1, 2, 3 ],
 [ 8, 9, 4 ],
 [ 7, 6, 5 ]
]

'''

class Solution(object):
    def generateMatrix(self, n):
        """
        :type n: int
        :rtype: List[List[int]]
        """
        if n == 0: return []
        
        m = [[0] * n for i in range(n)]
        
        pos = lambda idx: (idx // n, idx % n)
        
        direct = {0:1, 1:n, 2:-1, 3:-n}
        
        m[0][0] = 1
        count = 1
        i, d = 0, 0 # index 0, direct 0
        
        while count < n*n:
            nextidx = i + direct[d]
            r, c = pos(nextidx)
            if m[r][c] == 0:
                count += 1
                m[r][c] = count
                i = nextidx
                if r == 0 or r == n -1 or c == 0 or c == n -1:
                    d = (d + 1) % 4
            else:
                d = (d + 1) % 4
            
        return m
            

if __name__ == '__main__':
    s = Solution()
    m = s.generateMatrix(2)
    print(m)