'''
Created on 20160501

@author: Kenneth Tse

Find all possible combinations of k numbers that add up to a number n, given that only numbers from 1 to 9 can be used and each combination should be a unique set of numbers.

Ensure that numbers within the set are sorted in ascending order.


Example 1:

Input: k = 3, n = 7

Output:

[[1,2,4]]

Example 2:

Input: k = 3, n = 9

Output:

[[1,2,6], [1,3,5], [2,3,4]]

'''

class Solution(object):
    def combinationSum3(self, k, n):
        """
        :type k: int
        :type n: int
        :rtype: List[List[int]]
        """
        
        ret = []
        def search(start, cnt, sum, nums):
            if cnt == k and sum == n:
                ret.append(nums)
                return
            if cnt > k or sum > n:
                return
            
            for i in range(start +1, 10):
                search(i, cnt + 1, sum + i, nums + [i])
        search(0, 0, 0, [])
        return ret
        

if __name__ == '__main__':
    pass