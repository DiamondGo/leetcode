'''
Say you have an array for which the ith element is the price of a given stock on day i.

Design an algorithm to find the maximum profit. You may complete as many transactions as
 you like (ie, buy one and sell one share of the stock multiple times). However, you may 
 not engage in multiple transactions at the same time (ie, you must sell the stock before you buy again).
'''

class Solution:
    # @param prices, a list of integer
    # @return an integer
    def maxProfit(self, prices):
        if len(prices) <= 1:
            return 0
        curMin = prices[0]
        idx = 1
        while idx < len(prices) and prices[idx] <= curMin:
            curMin = prices[idx]
            idx += 1
        if idx == len(prices):
            return 0
        buyPrice = curMin
        curMax = prices[idx]
        idx += 1
        while idx < len(prices) and prices[idx] >= curMax:
            curMax = prices[idx]
            idx += 1
        # at idx price start fall
        return curMax - curMin + (self.maxProfit(prices[idx:]) if idx < len(prices) else 0)


if __name__ == '__main__':
    pass