'''
Created on 2015.8.9

@author: Kenneth Tse

Given a non-negative number represented as an array of digits, plus one to the number.

The digits are stored such that the most significant digit is at the head of the list.
'''

class Solution:
    # @param {integer[]} digits
    # @return {integer[]}
    def plusOne(self, digits):
        for i in range(len(digits) -1, -1, -1):
            if digits[i] != 9:
                digits[i] += 1
                break
            else:
                digits[i] = 0
                if i == 0:
                    digits = [1] + digits
                    break
        return digits
                

if __name__ == '__main__':
    print(Solution().plusOne([9]))