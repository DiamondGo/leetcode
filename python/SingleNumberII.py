'''
Created on 20160429

@author: Kenneth Tse

Given an array of integers, every element appears three times except for one. Find that single one.

'''

class Solution(object):
    def singleNumber(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        bitCount = [0] * 32
        for num in nums:
            bit = 0
            while num:
                if num < 0:
                    num = -num
                    neg = True
                else:
                    neg = False
                if num & 1:
                    if neg:
                        bitCount[bit] -= 1
                    else:
                        bitCount[bit] += 1
                num = num >> 1
                bit += 1
        
        n = 0
        for i in range(32):
            n += (2 ** i) * (bitCount[i] % 3)
        
        return n
        

if __name__ == '__main__':
    s = Solution()
    n = s.singleNumber([1])
    print(n)