'''
Created on 20160503

@author: Kenneth Tse

Given an array and a value, remove all instances of that value in place and return the new length.

Do not allocate extra space for another array, you must do this in place with constant memory.

The order of elements can be changed. It doesn't matter what you leave beyond the new length.

Example:
Given input array nums = [3,2,2,3], val = 3

Your function should return length = 2, with the first two elements of nums being 2.

Show Hint 


'''

class Solution(object):
    def removeElement(self, nums, val):
        """
        :type nums: List[int]
        :type val: int
        :rtype: int
        """

        """
        cur = 0

        def findNext(nl, v, start):
            while start < len(nl):
                if nl[start] == v:
                    return start
                else:
                    start += 1
            return -1
            
        def findNextNot(nl, v, start):
            while start < len(nl):
                if nl[start] != v:
                    return start
                else:
                    start += 1
            return -1
        
        
        while cur < len(nums):
            nextval = findNext(nums, val, cur)
            if nextval != -1: # got one
                nextnotval = findNextNot(nums, val, nextval +1)
            else:
                return len(nums) # no val from cur
            
            if nextnotval == -1:
                return nextval # no not-val from cur
            
            tmp = nextnotval
            while tmp < len(nums) and nums[tmp] != val:
                nums[nextval + tmp - nextnotval] = nums[tmp]
                nums[tmp] = val
                tmp += 1
            
            cur = tmp - (nextnotval - nextval)
        
        return cur
        """
        
        idx = 0
        
        for i in range(len(nums)):
            if nums[i] != val:
                nums[idx] = nums[i]
                idx += 1
        
        return idx
        

if __name__ == '__main__':
    s = Solution()
    print(s.removeElement([1,2,3,4], 2))