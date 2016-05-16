'''
Created on 20160430

@author: Kenneth Tse

Say you have an array for which the ith element is the price of a given stock on day i.

Design an algorithm to find the maximum profit. You may complete as many transactions as you like (ie, buy one and sell one share of the stock multiple times) with the following restrictions:

You may not engage in multiple transactions at the same time (ie, you must sell the stock before you buy again).
After you sell your stock, you cannot buy stock on next day. (ie, cooldown 1 day)
Example:

prices = [1, 2, 3, 0, 2]
maxProfit = 3
transactions = [buy, sell, cooldown, buy, sell]

'''

class Solution(object):
    def maxProfit(self, prices):
        """
        :type prices: List[int]
        :rtype: int
        """
        if prices is None or len(prices) < 2:
            return 0
        
        buydp = [0] * len(prices)
        selldp = [0] * len(prices)
        
        buydp[0:2] = [-prices[0], max(-prices[0], -prices[1])]
        selldp[0:2] = [0, max(0, prices[1] - prices[0])]
        
        for i in range(2, len(prices)):
            selldp[i] = max(selldp[i-1], buydp[i-1] + prices[i])
            buydp[i] = max(buydp[i-1], selldp[i-2] - prices[i])
        
        return selldp[-1]

if __name__ == '__main__':
    pass