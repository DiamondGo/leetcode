'''
Created on 20160505

@author: Kenneth Tse

Remove the minimum number of invalid parentheses in order to make the input string valid. Return all possible results.

Note: The input string may contain letters other than the parentheses ( and ).

Examples:
"()())()" -> ["()()()", "(())()"]
"(a)())()" -> ["(a)()()", "(a())()"]
")(" -> [""]

'''

class Solution(object):
    def removeInvalidParentheses(self, s):
        """
        :type s: str
        :rtype: List[str]
        """
        
        def calc(s):
            l = r = 0
            for ch in s:
                l += {'(':1, ')':-1}.get(ch, 0)
                if l < 0:
                    r += 1
                    l = 0
            return l + r
            
        visited = set()
        ans = []
        
        def dfs(s):
            mis = calc(s)
            if mis == 0:
                ans.append(s)
            
            for idx in range(len(s)):
                if s[idx] == ')' or s[idx] == '(':
                    subs = s[:idx] + s[idx + 1:]
                    submis = calc(subs)
                    if submis < mis:
                        visited.add(subs)
        dfs(s)
        return ans
                    

if __name__ == '__main__':
    s = Solution()
    print(s.removeInvalidParentheses("()())()"))