'''
Created on 2015Äê8ÔÂ9ÈÕ

@author: Kenneth Tse
'''
'''
There are two sorted arrays nums1 and nums2 of size m and n respectively.
Find the median of the two sorted arrays. The overall run time complexity should be O(log (m+n)).
'''

class Solution:
    # @param {integer[]} nums1
    # @param {integer[]} nums2
    # @return {float}
    def findMedianSortedArrays(self, nums1, nums2):
        m = len(nums1)
        n = len(nums2)
        
        if (m + n) % 2 != 0:
            return self.findKth(nums1, nums2, (m + n) / 2, 0, m -1, 0, n -1)
        else:
            return (self.findKth(nums1, nums2, (m + n) / 2, 0, m -1, 0, n -1) 
                    + self.findKth(nums1, nums2, (m + n) / 2 -1, 0, m -1, 0, n -1)) * 0.5
    
    def findKth(self, ary1, ary2, kth, start1, end1, start2, end2):
        len1 = end1 - start1 +1
        len2 = end2 - start2 +1
        
        if len1 == 0:
            return ary2[start2 + kth]
        if len2 == 0:
            return ary1[start1 + kth]
        if kth == 0:
            return ary1[start1] if ary1[start1] < ary2[start2] else ary2[start2]
        
        mid1 = len1 * kth / (len1 + len2)
        mid2 = kth - mid1 -1
        mid1 = mid1 + start1
        mid2 = mid2 + start2
        
        if ary1[mid1] > ary2[mid2]:
            kth = kth - (mid2 - start2 +1)
            end1 = mid1
            start2 = mid2 +1
        else:
            kth = kth - (mid1 - start1 +1)
            end2 = mid2
            start1 = mid1 +1
            
        return self.findKth(ary1, ary2, kth, start1, end1, start2, end2)

        

if __name__ == '__main__':
    pass