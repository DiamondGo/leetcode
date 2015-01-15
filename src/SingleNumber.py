class Solution:
    # @param A, a list of integer
    # @return an integer
    def singleNumber(self, A):
        n = 0
        for i in A:
            n = n^i
        return n


if __name__ == '__main__':
    pass
