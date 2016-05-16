'''
Created on 20160505

@author: Kenneth Tse



'''
# Definition for a binary tree node.
class TreeNode(object):
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

class Solution(object):
    def flatten(self, root):
        """
        :type root: TreeNode
        :rtype: void Do not return anything, modify root in-place instead.
        """
        
        
        def flattenNode(node): # return Head and Tail
            if node is None:
                return None, None
            
            head, tail = node, node
            
            lhead, ltail = flattenNode(node.left)
            rhead, rtail = flattenNode(node.right)

            if lhead is not None:
                tail.left = None
                tail.right = lhead
                tail = ltail
            
            rhead, rtail = flattenNode(node.right)
            if rhead is not None:
                tail.left = None
                tail.right = rhead
                tail = rtail
            
            return head, tail
        
        return flattenNode(root)[0]

if __name__ == '__main__':
    s = Solution()
    n0 = TreeNode(1)
    n1 = TreeNode(2)
    n0.left = n1
    
    s.flatten(n0)