'''
Created on 20150812

@author: Kenneth Tse

Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

The brackets must close in the correct order, "()" and "()[]{}" are all valid but "(]" and "([)]" are not.
'''
class Solution:
    # @param {string} s
    # @return {boolean}
    def __init__(self):
        self.cmap = {}
        self.cmap['('] = ')'
        self.cmap['['] = ']'
        self.cmap['{'] = '}'
        self.cvalues = set(self.cmap.values())
        
    def isValid(self, s):
        stack = []
        
        for c in s:
            if c in self.cmap:
                stack.append(c)
            else:
                if c in self.cvalues:
                    if len(stack) > 0 and self.cmap[stack[-1]] == c:
                        stack.pop()
                    else:
                        return False
                else:
                    return False
        
        return len(stack) == 0
        

if __name__ == '__main__':
    pass