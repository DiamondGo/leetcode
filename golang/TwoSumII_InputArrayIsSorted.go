package main

import "fmt"
/*
Given an array of integers that is already sorted in ascending order, find two numbers such that they add up to a specific target number.

The function twoSum should return indices of the two numbers such that they add up to the target, where index1 must be less than index2. Please note that your returned answers (both index1 and index2) are not zero-based.

You may assume that each input would have exactly one solution.

Input: numbers={2, 7, 11, 15}, target=9
Output: index1=1, index2=2
 */


func twoSum(numbers []int, target int) []int {
	s, e := 0, len(numbers) - 1
	for s < e {
		sum := s + e
		if sum < target {
			s++
		} else if sum > target {
			e--
		} else if sum == target {
			return []int{s+1, e+1}
		}
	}
	return []int{0, 0}
}

func main() {
	fmt.Println("hello")
}