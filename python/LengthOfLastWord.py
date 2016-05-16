'''
Created on 20160508

@author: Kenneth Tse

Given a string s consists of upper/lower-case alphabets and empty space characters ' ', return the length of last word in the string.

If the last word does not exist, return 0.

Note: A word is defined as a character sequence consists of non-space characters only.

For example, 
Given s = "Hello World",
return 5.
'''

class Solution(object):
    def lengthOfLastWord(self, s):
        """
        :type s: str
        :rtype: int
        """
        """
        words = s.split()
        return len(words[-1]) if len(words) > 0 else 0
        """
        
        def findSpace(string, idx, maxlen):
            first, last = -1, -1
            while idx < maxlen:
                if string[idx] != ' ':
                    if first != -1:
                        return first, last
                    idx += 1
                    continue
                if first == -1:
                    first = idx
                    last = idx
                else:
                    last = idx
                    idx += 1
            return first, last
        
        maxlen = len(s)
        
        spacel, spacer = findSpace(s, 0, maxlen)
        if spacel == -1:
            return maxlen
        
        if spacer == maxlen - 1:
            return spacel
            
        while True:
            nextl, nextr = findSpace(s, spacer + 1, maxlen)
            if nextl == -1:
                return maxlen -1 - spacer
            if nextr == maxlen -1:
                return nextl - spacer - 1
            
            spacel, spacer = nextl, nextr
        

if __name__ == '__main__':
    s = Solution()
    print(s.lengthOfLastWord(" "))