package main
/*
Given a binary tree, find its maximum depth.

The maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.
 */


//Definition for a binary tree node.
type TreeNode struct {
    Val int
    Left *TreeNode
    Right *TreeNode
}

func maxDepth(root *TreeNode) int {
    if root == nil {
        return 0
    }
    leftMax := maxDepth(root.Left)
    rightMax := maxDepth(root.Right)
    if leftMax > rightMax {
        return leftMax + 1
    } else{
        return rightMax + 1
    }
}

func main() {
}
