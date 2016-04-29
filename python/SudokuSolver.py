'''
Write a program to solve a Sudoku puzzle by filling the empty cells.

Empty cells are indicated by the character '.'.

You may assume that there will be only one unique solution.
'''

class Solution:
    # @param board, a 9x9 2D array
    # Solve the Sudoku by modifying the input board in-place.
    # Do not return any value.
    def solveSudoku(self, board):
        '''
        board = [[c for c in row] for row in board]
        
        rowCandi = [None] * 9
        columnCandi = [None] * 9
        
        for i in range(9):
            rowCandi[i] = set(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
            for j in range(9):
                try:
i                           print(candimap[i * 9 + j])
                    rowCandi[i].remove(board[i][j])
                except:
                    pass
        
        for j in range(9):
            columnCandi[j] = set(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
            for i in range(9):
                try:
                    columnCandi[j].remove(board[i][j])
                except:
                    pass
                
        foundSet = True
        while foundSet:
            print(board)
            foundSet = False
            for i in range(9):
                for j in range(9):
                    if board[i][j] == '.':
                        board[i][j] = rowCandi[i].intersection(columnCandi[j])
                        #print(board[i][j])
                        foundSet = True
                    
                    if isinstance(board[i][j], set):
                        foundSet = True
                        for oj in range(9):
                            if oj != j and isinstance(board[i][oj], str):
                                try:
                                    board[i][j].remove(board[i][oj])
                                except:
                                    pass
                        for oi in range(9):
                            if oi != i and isinstance(board[oi][j], str):
                                try:
                                    board[i][j].remove(board[oi][j])
                                except:
                                    pass
                        if len(board[i][j]) == 1:
                            board[i][j] = board[i][j].pop()
                            rowCandi[i].remove(board[i][j])
                            columnCandi[j].remove(board[i][j])
        '''
        candimap = {}
        certainmap = {}
        for i in range(9):
            for j in range(9):
                if board[i][j] == '.':
                    candimap[i * 9 + j] = set(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
                else:
                    certainmap[i * 9 + j] = board[i][j]
        print(len(candimap), len(certainmap))
        
        while len(candimap) > 0:
            for i in range(9):
                for j in range(9):
                    if i * 9 + j in candimap:
                        # check row
                        for k in range(9):
                            if k != j and i * 9 + k in certainmap:
                                try:
                                    candimap[i * 9 + j].remove(certainmap[i * 9 + k])
                                    #print(i * 9 + j, i * 9 + k)
                                except:
                                    pass
                        # check col
                        for k in range(9):
                            if k != i and k * 9 + j in certainmap:
                                try:
                                    candimap[i * 9 + j].remove(certainmap[k * 9 + j])
                                    #print(i * 9 + j, k * 9 + j)
                                except:
                                    pass
                        # check sandbox
                        m = (i // 3) * 3
                        n = (j // 3) * 3
                        for p in range(m, m + 3):
                            for q in range(n, n + 3):
                                if p * 9 + q != i * 9 + j and p * 9 + q in certainmap:
                                    try:
                                        candimap[i * 9 + j].remove(certainmap[p * 9 + q])
                                    except:
                                        pass
                        # check certain
                        if len(candimap[i * 9 + j]) == 1:
                            certainmap[i * 9 + j] = candimap[i * 9 + j].pop()
                            del candimap[i * 9 + j]
        
        for i in range(9):
            board[i] = "".join([certainmap[i * 9 + j] for j in range(9)])
        
        print(board)

if __name__ == '__main__':
    Solution().solveSudoku(["..9748...","7........",".2.1.9...","..7...24.",".64.1.59.",".98...3..","...8.3.2.","........6","...2759.."])
