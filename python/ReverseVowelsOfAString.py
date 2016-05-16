'''
Created on 20160501

@author: Kenneth Tse

Write a function that takes a string as input and reverse only the vowels of a string.

Example 1:
Given s = "hello", return "holle".

Example 2:
Given s = "leetcode", return "leotcede".

'''

class Solution(object):
    def reverseVowels(self, s):
        """
        :type s: str
        :rtype: str
        """
        # scan for vowels
        vpos = []
        for i in range(len(s)):
            if s[i] in ['a','e','i','o','u']:
                vpos.append(i)
        l = list(s)
        for i in range(len(vpos)//2):
            l[vpos[i]], l[vpos[len(vpos) -1 - i]] = l[vpos[len(vpos) -1 - i]], l[vpos[i]]
        
        return "".join(l)

if __name__ == '__main__':
    s = Solution()
    print(s.reverseVowels("aA"))