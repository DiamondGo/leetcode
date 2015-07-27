
class Solution:
    # @param {integer[]} nums
    # @param {integer} k
    # @return {void} Do not return anything, modify nums in-place instead.
    def rotate(self, nums, k):
        '''
        # method 1
        l = moved = len(nums)
        if l == 1 or k == 0:
            return
        startidx = 0
        while moved > 0:
            #nums[(idx + k) % l] = num
            idx = startidx
            pre = nums[idx]
            
            while True:
                nextidx = (idx + k) % l
                if nextidx == startidx:
                    nums[startidx] = pre
                    moved -= 1
                    startidx += 1
                    break
                nums[nextidx], pre = pre, nums[nextidx]
                moved -= 1
                if moved == 0:
                    break
                idx = nextidx
        '''
        # method 2
        l = len(nums)
        if k == 0 or l < 2:
            return
        k = k % l
        car, cdr = nums[:-k], nums[-k:]
        nums[:] = cdr + car



if __name__ == '__main__':
    nums = [1,2,3]
    k = 1
    Solution().rotate(nums, k)
    print(nums)