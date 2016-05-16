'''
Created on 20160511

@author: Kenneth Tse

Write a program to find the n-th ugly number.

Ugly numbers are positive numbers whose prime factors only include 2, 3, 5. For example, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12 is the sequence of the first 10 ugly numbers.

Note that 1 is typically treated as an ugly number.

Hint:

The naive approach is to call isUgly for every number until you reach the nth one. Most numbers are not ugly. Try to focus your effort on generating only the ugly ones.
An ugly number must be multiplied by either 2, 3, or 5 from a smaller ugly number.
The key is how to maintain the order of the ugly numbers. Try a similar approach of merging from three sorted lists: L1, L2, and L3.
Assume you have Uk, the kth ugly number. Then Uk+1 must be Min(L1 * 2, L2 * 3, L3 * 5).
'''

class Solution(object):
    def nthUglyNumber(self, n):
        """
        :type n: int
        :rtype: int
        """
        
        i2 = 1
        i3 = 1
        i5 = 1
        
        cur = 1
        n2 = 0
        n3 = 0
        n5 = 0
        
        uglylist = [1]
        count = 1
        while count < n:
            
            
            while uglylist[n2] * 2 <= cur:
                n2 += 1
            while uglylist[n3] * 3 <= cur:
                n3 += 1
            while uglylist[n5] * 5 <= cur:
                n5 += 1

            
            if uglylist[n2] * 2 < uglylist[n3] * 3 and uglylist[n2] * 2 < uglylist[n5] * 5:
                cur = uglylist[n2] * 2
                uglylist.append(cur)
                n2 += 1
            elif uglylist[n3] * 3 < uglylist[n5] * 5:
                cur = uglylist[n3] * 3
                uglylist.append(cur)
                n3 += 1
            else:
                cur = uglylist[n5] * 5
                uglylist.append(cur)
                n5 += 1
            count += 1
        
        #return cur
        return uglylist

if __name__ == '__main__':
    s = Solution()
    print(s.nthUglyNumber(37))