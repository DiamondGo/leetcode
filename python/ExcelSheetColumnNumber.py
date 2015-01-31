'''
Related to question Excel Sheet Column Title

Given a column title as appear in an Excel sheet, return its corresponding column number.

For example:

    A -> 1
    B -> 2
    C -> 3
    ...
    Z -> 26
    AA -> 27
    AB -> 28 
Credits:
Special thanks to @ts for adding this problem and creating all test cases.
'''

class Solution:
    numMap = dict([(ch, ord(ch) - ord("A") + 1) for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])
    
    # @param s, a string
    # @return an integer
    def titleToNumber(self, s):
        #numMap = dict([(ch, ord(ch) - ord("A") + 1) for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])
        sum = idx = 0
        while idx < len(s):
            sum += Solution.numMap[s[-1 - idx]] * 26**idx
            idx += 1
        return sum
            

if __name__ == '__main__':
    s = Solution()
    print(s.titleToNumber("AB"))