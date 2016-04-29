'''
Created on 20160429

@author: Kenneth Tse

Given n pairs of parentheses, write a function to generate all combinations of well-formed parentheses.

For example, given n = 3, a solution set is:

"((()))", "(()())", "(())()", "()(())", "()()()"

'''

from copy import copy

class Solution(object):
    def generateParenthesis(self, n):
        """
        :type n: int
        :rtype: List[str]
        """
        out = []
        comb = []
        self.findParenthesis(n, 0, 0, comb, out)
        return ["".join(comb) for comb in out]
    
    def findParenthesis(self, n, l, r, comb, out):
        if n == l == r:
            out.append(copy(comb))
            
        if l < n:
            comb.append("(")
            self.findParenthesis(n, l +1, r, comb, out)
            comb.pop()
        
        if r < l:
            comb.append(")")
            self.findParenthesis(n, l, r +1, comb, out)
            comb.pop()
            

if __name__ == '__main__':
    s = Solution()
    print(s.generateParenthesis(1))