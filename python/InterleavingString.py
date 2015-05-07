'''
Given s1, s2, s3, find whether s3 is formed by the interleaving of s1 and s2.

For example,
Given:
s1 = "aabcc",
s2 = "dbbca",

When s3 = "aadbbcbcac", return true.
When s3 = "aadbbbaccc", return false.
'''

class Solution:
    # @param {string} s1
    # @param {string} s2
    # @param {string} s3
    # @return {boolean}
    '''
    def isInterleave(self, s1, s2, s3):
        if len(s1) + len(s2) != len(s3):
            return False

        choiseStack = []
        # add start
        choiseStack.append((0,0,0))
        while len(choiseStack) > 0:
            p1, p2, p3 = choiseStack.pop()
            # check current char

            while p3 < len(s3):
                if p1 == len(s1):
                    if p2 < len(s2) and s2[p2:] == s3[p3:]:
                        return True
                    else:
                        break
                elif p2 == len(s2):
                    if p1 < len(s1) and s1[p1:] == s3[p3:]:
                        return True
                    else:
                        break
                #forward
                if s1[p1] == s3[p3] and s2[p2] != s3[p3]:
                    p1 += 1
                    p3 += 1
                    continue
                elif s1[p1] != s3[p3] and s2[p2] == s3[p3]:
                    p2 += 1
                    p3 += 1
                    continue
                elif s1[p1] != s3[p3] and s2[p2] != s3[p3]:
                    break
                else: #s1[p1] == s3[p3] and s2[p2] == s3[p3]:
                    choiseStack.append((p1 +1, p2, p3 +1))
                    choiseStack.append((p1, p2 +1, p3 +1))
                    break



            if p1 == len(s1) and p2 == len(s2) and p3 == len(s3):
                return True
        return False
        '''

    def isInterleave(self, s1, s2, s3):
        if len(s1) + len(s2) != len(s3):
            return False
        
        res = [[None] * (len(s2) + 1) for x in range(len(s1) + 1)]
        def interleaveOk(p1, p2):
            if p1 > len(s1) or p2 > len(s2):
                return False
            if res[p1][p2] is not None:
                return res[p1][p2]
            if p1 == len(s1):
                if s2[p2:] == s3[p1 + p2:]:
                    res[p1][p2] = True
                    return True
                else:
                    res[p1][p2] = False
                    return False
            if p2 == len(s2):
                if s1[p1:] == s3[p1 + p2:]:
                    res[p1][p2] = True
                    return True
                else:
                    res[p1][p2] = False
                    return False

            if s1[p1] == s3[p1 + p2]:
                if s2[p2] == s3[p1 + p2]:
                    ok = interleaveOk(p1 + 1, p2) or interleaveOk(p1, p2 + 1)
                else:
                    ok = interleaveOk(p1 + 1, p2) 
            else:
                if s2[p2] == s3[p1 + p2]:
                    ok = interleaveOk(p1, p2 + 1)
                else:
                    ok = False
            res[p1][p2] = ok
            return ok
        return interleaveOk(0, 0)


if __name__ == '__main__':
    #ret = Solution().isInterleave("aabaac", "aadaaeaaf", "aadaaeaabaafaac")
    #ret = Solution().isInterleave("aabcc", "dbbca", "aadbbcbcac")
    ret = Solution().isInterleave("aabcc", "dbbca", "aadbbbaccc")
    #ret = Solution().isInterleave("bbbbbabbbbabaababaaaabbababbaaabbabbaaabaaaaababbbababbbbbabbbbababbabaabababbbaabababababbbaaababaa", "babaaaabbababbbabbbbaabaabbaabbbbaabaaabaababaaaabaaabbaaabaaaabaabaabbbbbbbbbbbabaaabbababbabbabaab", "babbbabbbaaabbababbbbababaabbabaabaaabbbbabbbaaabbbaaaaabbbbaabbaaabababbaaaaaabababbababaababbababbbababbbbaaaabaabbabbaaaaabbabbaaaabbbaabaaabaababaababbaaabbbbbabbbbaabbabaabbbbabaaabbababbabbabbab")
    print(ret)