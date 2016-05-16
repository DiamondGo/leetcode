'''
Created on 20160430

@author: Kenneth Tse

Given a binary tree

    struct TreeLinkNode {
      TreeLinkNode *left;
      TreeLinkNode *right;
      TreeLinkNode *next;
    }
Populate each next pointer to point to its next right node. If there is no next right node, the next pointer should be set to NULL.

Initially, all next pointers are set to NULL.

Note:

You may only use constant extra space.
You may assume that it is a perfect binary tree (ie, all leaves are at the same level, and every parent has two children).
For example,
Given the following perfect binary tree,
         1
       /  \
      2    3
     / \  / \
    4  5  6  7
After calling your function, the tree should look like:
         1 -> NULL
       /  \
      2 -> 3 -> NULL
     / \  / \
    4->5->6->7 -> NULL

'''

# Definition for binary tree with next pointer.
# class TreeLinkNode(object):
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None
#         self.next = None

class Solution(object):
    def connect(self, root):
        """
        :type root: TreeLinkNode
        :rtype: nothing
        """
        if root is None: return
        
        parent = root
        first = root.left
        nodecount = 0
        
        while first:
            tmp = first
            while True:
                nodecount += 1
                if nodecount % 2 == 1:
                    tmp.next = parent.right
                    tmp = parent.right
                else:
                    if parent.next:
                        parent = parent.next
                        tmp.next = parent.left
                        tmp = parent.left
                    else:
                        # rewind
                        tmp.next = None
                        parent = first
                        first = parent.left
                        break
                
            
            
            

            
        
        

if __name__ == '__main__':
    s = Solution()
    l = [1,2,3]