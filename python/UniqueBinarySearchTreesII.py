'''
Created on 20160509

@author: Kenneth Tse

Given n, generate all structurally unique BST's (binary search trees) that store values 1...n.

For example,
Given n = 3, your program should return all 5 unique BST's shown below.

   1         3     3      2      1
    \       /     /      / \      \
     3     2     1      1   3      2
    /     /       \                 \
   2     1         2                 3
confused what "{1,#,2,3}" means? > read more on how binary tree is serialized on OJ.
'''

# Definition for a binary tree node.
class TreeNode(object):
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

class Solution(object):
    def generateTrees(self, n):
        """
        :type n: int
        :rtype: List[TreeNode]
        """
        if n < 1: return []
        
        dp = [[[]] * n for i in range(n)] # dp[i][j] result of list of all bst from node i to node j
        
        def allBST(start, end):
            if start > end:
                return [None]
            if dp[start][end] != []:
                return dp[start][end]
            if start == end:
                node = TreeNode(start + 1)
                dp[start][end] = [node]
                return dp[start][end]
            
            ans = []
            for i in range(start, end +1):
                leftChildren = allBST(start, i - 1)
                rightChildren = allBST(i + 1, end)
                for l in leftChildren:
                    for r in rightChildren:
                        node = TreeNode(i + 1)
                        node.left = l
                        node.right = r
                        ans.append(node)
            dp[start][end] = ans
            return ans
        
        return allBST(0, n-1)

if __name__ == '__main__':
    s = Solution()
    
    print(s.generateTrees(2))