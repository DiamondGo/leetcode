'''
Created on 20160502

@author: Kenneth Tse

Given n non-negative integers a1, a2, ..., an, where each represents a point at coordinate (i, ai). n vertical lines are drawn such that the two endpoints of line i is at (i, ai) and (i, 0). Find two lines, which together with x-axis forms a container, such that the container contains the most water.

'''

class Solution(object):
    def maxArea(self, height):
        """
        :type height: List[int]
        :rtype: int
        """
        #(x2 - x1) * min(x2, x1)
        
        """
        maxwater = 0
        for i in range(len(height)):
            for j in range(i+1, len(height)):
                maxwater = max(maxwater, min(height[i], height[j]) * (j - i))
        
        return maxwater
        """
        if height is None or len(height) < 2: return 0
        
        i = 0
        j = len(height) -1
        
        #hl = height[i]
        #hr = height[j]
        
        maxwater = 0
        
        while j > i:
            tmp =min(height[i], height[j]) * (j - i)
            maxwater = max(maxwater, tmp)
            
            if j == i + 1:
                break
            
            if height[i] < height[j]: # move i to right
                """
                for k in range(i+1, j):
                    i = k
                    if height[k] > height[i]:
                        hl = height[k]
                        break
                        """
                while height[i+1] <= height[i] and i < j:
                    i += 1
                i += 1
            else:
                """
                for k in range(j -1, i, -1):
                    j = k
                    if height[k] > height[j]:
                        hr = height[k]
                        break
                """
                while height[j-1] <= height[j] and j > i:
                    j -= 1
                j -= 1
            
        
        return maxwater
                
        

if __name__ == '__main__':
    s = Solution()
    print(s.maxArea([1,2,1]))