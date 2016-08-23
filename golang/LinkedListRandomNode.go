package main
import "math/rand"
/*
Given a singly linked list, return a random node's value from the linked list. Each node must have the same probability of being chosen.

Follow up:
What if the linked list is extremely large and its length is unknown to you? Could you solve this efficiently without using extra space?

Example:

// Init a singly linked list [1,2,3].
ListNode head = new ListNode(1);
head.next = new ListNode(2);
head.next.next = new ListNode(3);
Solution solution = new Solution(head);

// getRandom() should return either 1, 2, or 3 randomly. Each element should have equal probability of returning.
solution.getRandom();
 */
/**
 * Definition for singly-linked list.
 */
type ListNode struct {
    Val int
    Next *ListNode
}

type Solution struct {
    Head *ListNode
    Size int
}


/** @param head The linked list's head.
        Note that the head is guaranteed to be not null, so it contains at least one node. */
func Constructor(head *ListNode) Solution {
    s := Solution{Head:head, Size:0}
    return s
}


/** Returns a random node's value. */
func (this *Solution) GetRandom() int {
    idx := rand.Int()
    if this.Size == 0 {
        for tmp, i := this.Head, 0; i <= idx; {
            if tmp.Next == nil {
                this.Size = i + 1
                break
            } else {
                if i == idx {
                    return tmp.Val
                }
                tmp = tmp.Next
                i += 1
            }
        }
    }
    idx = idx % this.Size
    tmp:= this.Head
    for i := 0; i < idx; i, tmp = i+1, tmp.Next {
    }
    return tmp.Val
}


/**
 * Your Solution object will be instantiated and called as such:
 * obj := Constructor(head);
 * param_1 := obj.GetRandom();
 */

func main() {
}
