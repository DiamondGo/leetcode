'''
Created on 20150817

@author: Kenneth Tse

Determine whether an integer is a palindrome. Do this without extra space.
'''
import math
class Solution:
    # @param {integer} x
    # @return {boolean}
    def isPalindrome(self, x):
        if x <= 0:
            return x == 0
        
        maxidx = int(math.log10(x))
        
        r = (maxidx + 1) //2
        
        digit = lambda x, y : x // 10**y % 10
        for i in range(r):
            if digit(x, i) != digit(x, maxidx - i):
                return False
            
        return True
        

if __name__ == '__main__':
    pass