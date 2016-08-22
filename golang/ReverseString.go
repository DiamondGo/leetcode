package main
/*
Write a function that takes a string as input and returns the string reversed.

Example:
Given s = "hello", return "olleh".

Subscribe to see which companies asked this question
 */

func reverseString(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes) - 1; i < j; i,j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}

func main() {

}
