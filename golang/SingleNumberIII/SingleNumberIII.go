package main

import "fmt"
/*
Given an array of numbers nums, in which exactly two elements appear only once and all the other elements appear exactly twice. Find the two elements that appear only once.

For example:

Given nums = [1, 2, 1, 3, 2, 5], return [3, 5].

Note:
The order of the result is not important. So in the above example, [5, 3] is also correct.
Your algorithm should run in linear runtime complexity. Could you implement it using only constant space complexity?
 */

func singleNumber(nums []int) []int {
	sum := 0
	for _, num := range nums {
		sum ^= num
	}

	mask := sum - (sum & (sum -1)) // last 1 bit
	sum1, sum2 := 0, 0
	for _, num := range nums {
		if num & mask == 0 {
			sum1 ^= num
		} else {
			sum2 ^= num
		}
	}
	return []int{sum1, sum2}
}

func main() {
	fmt.Println(singleNumber([]int{1}))
}
