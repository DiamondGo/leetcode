'''
Created on 20160426

@author: Kenneth Tse

Given a positive integer n, break it into the sum of at least two positive integers and maximize the product of those integers. Return the maximum product you can get.

For example, given n = 2, return 1 (2 = 1 + 1); given n = 10, return 36 (10 = 3 + 3 + 4).

'''

class Solution(object):
    def integerBreak(self, n):
        """
        :type n: int
        :rtype: int
        """
        if n <= 3:
            return n -1
        dp = [1] * (n +1)
        dp[2] = 2
        dp[3] = 3
        for i in range(4, n +1):
            dp[i] = max(dp[i -2] * 2, dp[i -3] * 3)
        return dp[n]

if __name__ == '__main__':
    pass