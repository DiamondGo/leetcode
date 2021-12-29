'''
Created on 2015��8��6��

@author: Kenneth Tse
'''
#from _overlapped import NULL

'''
Write a function to find the longest common prefix string amongst an array of strings.
'''

"""
class Solution:
    # @param {string[]} strs
    # @return {string}
    def longestCommonPrefix(self, strs):
        if strs is None or len(strs) == 0 or strs[0] == None or len(strs[0]) == 0:
            return ""
        if len(strs) == 1:
            return strs[0]
        
        idx = 0
        while True:
            ch = strs[0][idx]
            for id in range(1, len(strs)):
                if len(strs[id]) <= idx:
                    return strs[0][:idx]
                if strs[id][idx] != ch:
                    return strs[0][:idx]
            idx += 1
            if idx >= len(strs[0]):
                return strs[0]
"""
from typing import List

class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        index: int = 0
        if len(strs) == 1:
            return strs[0]
        breakouterloop = False
        while index < len(strs[0]) and not breakouterloop:
            for i in range(1, len(strs)):
                if index >= len(strs[i]) or strs[0][index] != strs[i][index]:
                    breakouterloop = True
                    break
            if not breakouterloop:
                index += 1       
        return strs[0][0:index]

if __name__ == '__main__':
    input = ["flower","flow","flight"]
    s = Solution()
    print(s.longestCommonPrefix(input))