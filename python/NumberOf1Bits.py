'''
Created on 20160429

@author: Kenneth Tse

Write a function that takes an unsigned integer and returns the number of ¡¯1' bits it has (also known as the Hamming weight).

For example, the 32-bit integer ¡¯11' has binary representation 00000000000000000000000000001011, so the function should return 3.


'''

class Solution(object):
    def hammingWeight(self, n):
        """
        :type n: int
        :rtype: int
        """
        asn = 0
        while n:
            if n & 1:
                asn += 1
            n = n >> 1

        return asn

if __name__ == '__main__':
    pass