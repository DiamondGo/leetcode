'''
Created on 20160430

@author: Kenneth Tse

Say you have an array for which the ith element is the price of a given stock on day i.

If you were only permitted to complete at most one transaction (ie, buy one and sell one share of the stock), design an algorithm to find the maximum profit.

'''

class Solution(object):
    def maxProfit(self, prices):
        """
        :type prices: List[int]
        :rtype: int
        """
        if prices is None or len(prices) < 2: return 0
        minprice = min(prices[0], prices[1])
        maxprofit = max(0, prices[1] - prices[0])
        for i in range(2, len(prices)):
            maxprofit = max(maxprofit, prices[i] - minprice)
            minprice = min(minprice, prices[i])
        
        return maxprofit
        

if __name__ == '__main__':
    pass