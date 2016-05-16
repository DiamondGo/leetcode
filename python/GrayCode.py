'''
Created on 20160501

@author: Kenneth Tse

The gray code is a binary numeral system where two successive values differ in only one bit.

Given a non-negative integer n representing the total number of bits in the code, print the sequence of gray code. A gray code sequence must begin with 0.

For example, given n = 2, return [0,1,3,2]. Its gray code sequence is:

00 - 0
01 - 1
11 - 3
10 - 2

'''

class Solution(object):
    def grayCode(self, n):
        """
        :type n: int
        :rtype: List[int]
        """
        if n == 0: return []
        if n == 1: return [0, 1]
        
        l = self.grayCode(n -1)
        return [code * 2 for code in l] + [code * 2 + 1 for code in reversed(l)]

if __name__ == '__main__':
    pass