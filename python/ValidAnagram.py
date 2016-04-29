'''
Created on 20160426

@author: Kenneth Tse

iven two strings s and t, write a function to determine if t is an anagram of s.

For example,
s = "anagram", t = "nagaram", return true.
s = "rat", t = "car", return false.

Note:
You may assume the string contains only lowercase alphabets.

Follow up:
What if the inputs contain unicode characters? How would you adapt your solution to such case?

'''
class Solution(object):
    def isAnagram(self, s, t):
        """
        :type s: str
        :type t: str
        :rtype: bool
        """
        lmap = {}
        for l in s:
            cnt = lmap.setdefault(l, 0)
            lmap[l] = cnt +1
        for l in t:
            cnt = lmap.setdefault(l, 0)
            lmap[l] = cnt -1
        
        for x in lmap.values():
            if x != 0:
                return False
        return True

if __name__ == '__main__':
    pass