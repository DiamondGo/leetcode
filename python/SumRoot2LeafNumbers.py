'''
Created on 20160504

@author: Kenneth Tse

Given a binary tree containing digits from 0-9 only, each root-to-leaf path could represent a number.

An example is the root-to-leaf path 1->2->3 which represents the number 123.

Find the total sum of all root-to-leaf numbers.

For example,

    1
   / \
  2   3
The root-to-leaf path 1->2 represents the number 12.
The root-to-leaf path 1->3 represents the number 13.

Return the sum = 12 + 13 = 25.

'''

# Definition for a binary tree node.
class TreeNode(object):
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

class Solution(object):
    def sumNumbers(self, root):
        """
        :type root: TreeNode
        :rtype: int
        """
        if root is None: return 0
        
        def allPath(node):
            if node.left is None and node.right is None:
                return [(1, node.val)] # depth val
            
            ret = []
            for child in [node.left, node.right]:
                if child:
                    childRet = allPath(child)
                    for depth, val in childRet:
                        ret.append((depth+1, 10 ** depth * node.val + val))
            
            return ret
        
        
        rootRet = allPath(root)
        
        return sum(map(lambda x: x[1], rootRet))

if __name__ == '__main__':
    s = Solution()
    
    n0 = TreeNode(0)
    n1 = TreeNode(1)
    n0.left = n1
    
    print(s.sumNumbers(n0))