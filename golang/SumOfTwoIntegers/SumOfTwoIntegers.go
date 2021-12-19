package main

import "fmt"
/*
Calculate the sum of two integers a and b, but you are not allowed to use the operator + and -.

Example:
Given a = 1 and b = 2, return 3.
 */

func getSum(a int, b int) int {
    currentbit := a ^ b
    forwordbit := (a & b) << 1
    if forwordbit == 0 {
        return currentbit
    } else {
        return getSum(currentbit, forwordbit)
    }
}

func main() {
    fmt.Println(getSum(100, 97))
}
