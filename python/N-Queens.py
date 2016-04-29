'''
Created on 20160428

@author: Kenneth Tse

The n-queens puzzle is the problem of placing n queens on an nxn chessboard such that no two queens attack each other.



Given an integer n, return all distinct solutions to the n-queens puzzle.

Each solution contains a distinct board configuration of the n-queens' placement, where 'Q' and '.' both indicate a queen and an empty space respectively.

For example,
There exist two distinct solutions to the 4-queens puzzle:

[
 [".Q..",  // Solution 1
  "...Q",
  "Q...",
  "..Q."],

 ["..Q.",  // Solution 2
  "Q...",
  "...Q",
  ".Q.."]
]

'''

from copy import deepcopy

class Solution(object):

    def solveNQueens(self, n):
        """
        :type n: int
        :rtype: List[List[str]]
        """
        if n == 1: return [['Q']]
        
        boardStack = []
        #init
        for col in range(n):
            board = [([0] * n) for i in range(n)]
            self.play(n, board, 0, col)
            boardStack.append((0, board))
            
        output = []
        while len(boardStack) > 0:
            row, board = boardStack.pop()
            for col in range(n):
                if board[row +1][col] == 0: # can play
                    newboard = deepcopy(board)
                    self.play(n, newboard, row +1, col)
                    if row +1 == n -1:
                        output.append(newboard)
                    else:
                        boardStack.append((row +1, newboard))
                
        ret = []
        m = {-1:".", 0:".", 1:"Q"}
        for rawsol in output:
            sol = []
            for row in rawsol:
                sol.append("".join([m[i] for i in row]))
            ret.append(sol)
        return ret
        

            
                
        

    
    def play(self, n, board, row, col):
        if board[row][col] != 0: # invalid position
            return False
        board[row][col] = 1
        for i in range(n):
            # row and col
            if i != row: board[i][col] = -1
            if i != col: board[row][i] = -1
            # sneak
            if i != row:
                # left
                coli = col - (row - i)
                if 0 <= coli < n:
                    board[i][coli] = -1
                # right
                coli = col + (row - i)
                if 0 <= coli < n:
                    board[i][coli] = -1
        return True

                    


        

        

if __name__ == '__main__':
    s = Solution()
    out = s.solveNQueens(1)
    print(out)