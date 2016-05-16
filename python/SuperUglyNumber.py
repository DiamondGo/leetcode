'''
Created on 20160502

@author: Kenneth Tse

Super ugly numbers are positive numbers whose all prime factors are in the given prime list primes of size k. For example, [1, 2, 4, 7, 8, 13, 14, 16, 19, 26, 28, 32] is the sequence of the first 12 super ugly numbers given primes = [2, 7, 13, 19] of size 4.


'''
class Solution(object):
    def nthSuperUglyNumber(self, n, primes):
        """
        :type n: int
        :type primes: List[int]
        :rtype: int
        """
        if n == 1: return 1
        
        cur = [1]
        nextmap = dict([(p, p) for p in primes if p > 1])

        
        def findNextMin(uglylist, k):
            fact = uglylist[-1] // k
            # find a num bigger than fact in list
            return findBigger(uglylist, 0, len(uglylist) -1, fact) * k
        
        def findBigger(l, s, e, f):
            if s >= e:
                return l[e]
            m = (s + e) // 2
            if l[m] <= f:
                return findBigger(l, m+1, e, f)
            else:
                return findBigger(l, s, m, f)
                
        while len(cur) < n:
            minpnext = 0
            for p in primes:
               pnext = nextmap[p]
               if pnext <= cur[-1]:
                   # find next min
                   pnext = findNextMin(cur, p)
                   nextmap[p] = pnext
               if minpnext == 0 or (pnext < minpnext and minpnext > 0):
                   minpnext = pnext
            cur.append(minpnext)
               
        return cur[-1]
    
if __name__ == '__main__':
    s = Solution()
    #print(s.nthSuperUglyNumber(3, [2,3,5]))
    print(s.nthSuperUglyNumber(10000, [7,19,29,37,41,47,53,59,61,79,83,89,101,103,109,127,131,137,139,157,167,179,181,199,211,229,233,239,241,251]))