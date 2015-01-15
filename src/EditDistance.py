class Solution:
    # @return an integer
    def minDistance(self, word1, word2):
        dismap = [-1] * ((1 + len(word1)) * (1 + len(word2)))
        index = lambda i, j : j * (len(word1) + 1) + i
        dis = lambda i, j : dismap[j * (len(word1) + 1) + i]
        for i in range(len(word1) + 1):
            for j in range(len(word2) + 1):
                if i == 0:
                    dismap[index(i, j)] = j
                elif j == 0:
                    dismap[index(i, j)] = i
                else:
                    dismap[index(i, j)] = min(dis(i-1, j) + 1, dis(i, j-1) + 1, dis(i-1, j-1) + (0 if word1[i-1] == word2[j-1] else 1))
        return dis(len(word1), len(word2))

if __name__ == '__main__':
    pass