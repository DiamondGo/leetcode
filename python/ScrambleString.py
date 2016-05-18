"""
Given a string s1, we may represent it as a binary tree by partitioning it to two non-empty substrings recursively.

Below is one possible representation of s1 = "great":

    great
   /    \
  gr    eat
 / \    /  \
g   r  e   at
           / \
          a   t
To scramble the string, we may choose any non-leaf node and swap its two children.

For example, if we choose the node "gr" and swap its two children, it produces a scrambled string "rgeat".

    rgeat
   /    \
  rg    eat
 / \    /  \
r   g  e   at
           / \
          a   t
We say that "rgeat" is a scrambled string of "great".

Similarly, if we continue to swap the children of nodes "eat" and "at", it produces a scrambled string "rgtae".

    rgtae
   /    \
  rg    tae
 / \    /  \
r   g  ta  e
       / \
      t   a
We say that "rgtae" is a scrambled string of "great".

Given two strings s1 and s2 of the same length, determine if s2 is a scrambled string of s1.
"""


class Solution(object):
    def isScramble(self, s1, s2):
        """
        :type s1: str
        :type s2: str
        :rtype: bool
        """
        # def countSame(s1, s2, f1, t1, f2, t2):

        if s1 == s2:
            return True

        for i in range(1, len(s1)):
            s1l, s1r = s1[:i], s1[i:]
            s2l, s2r = s2[:i], s2[i:]
            s3l, s3r = s2[:len(s1) - i], s2[len(s1) - i:]
            if (self.isScramble(s1l, s2l) and self.isScramble(s1r, s2r)) or (
                self.isScramble(s1l, s3r) and self.isScramble(s1r, s3l)):
                return True

        return False

if __name__ == "__main__":
    s = Solution()
    print(s.isScramble("abcdefghijklmn", "efghijklmncadb"))
    #print(s.isScramble("gtrea", "great"))