"""
There are a total of n courses you have to take, labeled from 0 to n - 1.

Some courses may have prerequisites, for example to take course 0 you have to first take course 1, which is expressed as a pair: [0,1]

Given the total number of courses and a list of prerequisite pairs, is it possible for you to finish all courses?

For example:

2, [[1,0]]
There are a total of 2 courses to take. To take course 1 you should have finished course 0. So it is possible.

2, [[1,0],[0,1]]
There are a total of 2 courses to take. To take course 1 you should have finished course 0, and to take course 0 you should also have finished course 1. So it is impossible.
"""


class Solution(object):
    def canFinish(self, numCourses, prerequisites):
        """
        :type numCourses: int
        :type prerequisites: List[List[int]]
        :rtype: bool
        """

        edgeMap = {}

        for f, t in prerequisites:
            tset = edgeMap.setdefault(f, set())
            tset.add(t)

        visited = [False] * numCourses

        for f in edgeMap:
            if visited[f]:
                continue
            stack = []
            stack.append(f)
            onStack = [False] * numCourses
            onStack[f] = True
            visited[f] = True

            while len(stack) > 0:
                fidx = stack[-1]  # peek
                allVisit = True
                tset = edgeMap.get(fidx, None)
                if tset is None:
                    stack.pop()
                    onStack[fidx] = False
                    continue
                for t in tset:
                    if onStack[t]:
                        return False
                    if not visited[t]:
                        visited[t] = True
                        allVisit = False
                        stack.append(t)
                        onStack[t] = True
                        continue
                if allVisit:
                    stack.pop()
                    onStack[fidx] = False

        return True

if __name__ == '__main__':
    s = Solution()
    print(s.canFinish(2, [[1,0]]))
