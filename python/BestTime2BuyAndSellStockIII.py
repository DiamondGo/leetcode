'''
Created on 20160430

@author: Kenneth Tse

Say you have an array for which the ith element is the price of a given stock on day i.

Design an algorithm to find the maximum profit. You may complete at most two transactions.

'''

class Solution(object):
    def maxProfit(self, prices):
        """
        :type prices: List[int]
        :rtype: int
        """
        if prices is None or len(prices) < 2: return 0
        dpforward = [0] * len(prices)
        dpbackword = [0] * len(prices)
        # forward 
        minprice = min(prices[0], prices[1])
        dpforward[0] = 0
        dpforward[1] = max(0, prices[1] - prices[0])
        for i in range(2, len(prices)):
            dpforward[i] = max(dpforward[i-1], prices[i] - minprice)
            minprice = min(minprice, prices[i])
            
        # backword
        maxprice = max(prices[-2], prices[-1])
        minprice = prices[-2]
        dpbackword[-1] = 0
        dpbackword[-2] = max(0, prices[-1] - prices[-2]);
        for i in range(-3, -len(prices), -1):
            if prices[i] < minprice:
                dpbackword[i] = maxprice - prices[i]
                minprice = prices[i]
            if prices[i] > maxprice:
                maxprice = prices[i]
            dpbackword[i] = max(maxprice - prices[i], dpbackword[i+1])
        
        maxcomb = 0
        for i in range(2, len(prices) -1):
            comb = dpforward[i -1] + dpbackword[i]
            maxcomb = max(maxcomb, comb)
            
        return max(maxcomb, dpforward[len(prices)-1])

        

        



if __name__ == '__main__':
    s = Solution()
    maxp = s.maxProfit([8,6,4,3,3,2,3,5,8,3,8,2,6])
    print(maxp)