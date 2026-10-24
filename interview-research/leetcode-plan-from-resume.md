# 根据简历准备的 LeetCode 刷题清单

> 整理日期：2026-10-24
>
> **这份清单是怎么来的**
> - 依据你的简历（后端与分布式系统、拓扑服务、乱序更新过滤、订阅管理、流式处理、查询改写、存储引擎、Go 传输库等），以及你仓库 `python/`、`golang/`、`cplusplus/` 目录里已有的约 117 道解答（我只能从文件名判断，你可能在别处也刷过）。
> - **你已经做过的题也都放进了清单**，用"状态"一列标成"已做"，你对这些只需要复习；"新题"才是需要新做的。
> - **题号和难度凭我的记忆整理，没有逐题联网核实**，以 LeetCode 上的题名为准；标注"会员"的题需要订阅才能看。
> - 简历里的联系方式我没有写进这份文档。

## 先说结论

1. **你的强项**：链表、动态规划（股票系列、编辑距离、戳气球）、回溯（N 皇后、数独）、位运算。这些已做的题，只要复习，不用重新学。
2. **你的明显缺口**：堆（heap）、图（graph）、前缀树（trie）、区间（intervals）、设计题（design）、二分查找的变形、单调栈、并发。这些恰好是中等难度面试题里最常见的，也是你的简历最容易被追问的方向。
3. **最值得优先练的是图和设计题**：你现在做的拓扑服务（topology services）天然对应图算法；乱序更新过滤、订阅管理、批处理对应设计题和流式数据结构。把简历里的经历接上算法题，是资深面试里很加分的讲法。
4. 清单一共 **278** 道题（含 10 道会员题），其中**新题 162 道、已做（复习）116 道**。

| 优先级 | 新题 | 已做（复习） | 含义 |
|---|---|---|---|
| P0 | 38 | 25 | 必做：面试出现概率最高，或和你的简历最贴近 |
| P1 | 67 | 43 | 强烈建议 |
| P2 | 57 | 48 | 有时间再做，或作为进阶、热身 |
| 合计 | 162 | 116 | |

## 你仓库现状的粗略统计

下面是我根据文件名做的**大致**分类，数字是约数。

| 主题 | 已做（约） | 评价 |
|---|---|---|
| 链表 | 16 | 很扎实 |
| 动态规划 | 22 | 很扎实，而且做过不少难题 |
| 回溯 | 12 | 扎实 |
| 数组、双指针、字符串、哈希 | 24 | 基础够，窗口类变形不足 |
| 二叉树 | 15 | 遍历和构造够，缺层序、普通树的最近公共祖先、路径和 |
| 位运算与数学 | 16 | 足够，不必再练 |
| 二分查找 | 4 | 偏少，缺旋转数组、在答案上二分 |
| 图 | 2 | **严重不足** |
| 栈、队列、设计 | 4 | **不足** |
| 堆 | 0 | **空白** |
| 前缀树 | 0 | **空白** |
| 区间 | 0 | **空白** |
| 并发、SQL | 0 | **空白** |

另外，你仓库里的题多是早年的经典题，代码风格（比如 Python 2 时代的写法）和现在面试常用的写法有差距。建议复习时**统一用 Python 3 加标准库**（`heapq`、`collections.deque`、`defaultdict`、`Counter`、`bisect`、`functools.lru_cache`）重写一遍，并熟悉每种数据结构的复杂度。面试里不能用第三方库（比如 `sortedcontainers`）。

## 简历经历与题型的对应

面试官经常顺着简历出题或追问。下面是你的经历对应的题型，以及后面的题单里相应的主题。

| 你简历里的经历 | 面试官可能怎么接 | 对应主题 |
|---|---|---|
| Arista：拓扑服务（CVaaS topology）、13 个区域集群、上万台设备 | 网络拓扑、连通性、关键链路、依赖关系 | 七、图 |
| Arista：乱序更新过滤，限制内存增长，消除 OOM | 序号和时间戳、去重、有界内存、窗口 | 十二、设计题（Stock Price Fluctuation、Ordered Stream）；六、区间（352）；二、哈希 |
| Arista：订阅管理器，统一封装 gRPC 流和数据库路径 | 发布订阅、引用计数、多订阅者共享一个连接 | 十二、设计题（LFU、Design Twitter）；五、堆 |
| Arista：按事件更新改为定时批量更新 | 合并更新、批处理、定时刷新 | 五、堆（Task Scheduler）；六、区间 |
| AWS：Engine Config Service、快速部署服务 | 依赖编排、任务调度、有向无环图 | 七、图（拓扑排序）；六、区间（1235） |
| AWS：Performance Insights 和 Enhanced Monitoring 的指标 | 时间序列聚合、滑动窗口、限流 | 二、滑动窗口；十二、设计题（Tweet Counts、Hit Counter） |
| 阿里：DMP 数据管理平台、nearline 计算、在线学习 | 流式统计、中位数、top-k、多路归并 | 五、堆（Median from Data Stream、Merge k Lists） |
| 阿里：广告搜索的查询改写服务 | 前缀树、编辑距离、分词、自动补全 | 十一、前缀树；十、动态规划（Edit Distance、Word Break） |
| 阿里：广告 cookie 映射、深度神经网络预测 | 采样、哈希、在线服务 | 十三、采样 |
| 网易：自研 MySQL 存储引擎 NTSE（C++） | 跳表、B 树、缓存、哈希表、版本化存储 | 十二、设计题（Skiplist、LFU、HashMap、Snapshot Array） |
| Go 传输库：HTTP 长轮询虚拟连接、多路复用 | 并发、有界队列、环形缓冲、死锁 | 十四、并发；十二、设计题（Circular Queue） |
| 技能里写了 SQL | 电话面或笔试的 SQL 题 | 十五、SQL |

## 题单

**优先级**：P0 必做，P1 强烈建议，P2 有时间再做。**状态**："新题"是你仓库里没有的；"已做"是你仓库里已有解答，复习即可。题名用英文，在 LeetCode 上直接搜索。同一优先级里，新题排在已做之前。

### 一、链表（linked list）

你的链表基础很扎实（仓库里做过十几道）。这里主要是复习，另补两道最常见的但仓库里没有的：Reverse Linked List 和 Add Two Numbers。

本主题：18 题（新题 3，已做 15）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 206 | Reverse Linked List | 简单 | P0 | 新题 | 最基础的反转，迭代和递归都要会 |
| 2 | Add Two Numbers | 中等 | P0 | 新题 | 链表加法，进位处理 |
| 21 | Merge Two Sorted Lists | 简单 | P0 | 已做 | 合并，是很多题的积木 |
| 141 | Linked List Cycle | 简单 | P0 | 已做 | 快慢指针 |
| 25 | Reverse Nodes in k-Group | 困难 | P0 | 已做 | 指针操作的综合题，面试常出 |
| 148 | Sort List | 中等 | P1 | 新题 | 链表上的归并排序 |
| 142 | Linked List Cycle II | 中等 | P1 | 已做 | 找环的入口，要能讲清证明 |
| 19 | Remove Nth Node From End of List | 中等 | P1 | 已做 | 前后双指针 |
| 92 | Reverse Linked List II | 中等 | P1 | 已做 | 局部反转 |
| 138 | Copy List with Random Pointer | 中等 | P1 | 已做 | 哈希或原地拼接 |
| 143 | Reorder List | 中等 | P1 | 已做 | 找中点加反转加合并 |
| 160 | Intersection of Two Linked Lists | 简单 | P1 | 已做 | 双指针 |
| 234 | Palindrome Linked List | 简单 | P1 | 已做 | 中点加反转 |
| 82 | Remove Duplicates from Sorted List II | 中等 | P1 | 已做 | 哨兵节点 |
| 83 | Remove Duplicates from Sorted List | 简单 | P2 | 已做 | 热身 |
| 328 | Odd Even Linked List | 中等 | P2 | 已做 | 拆分与重连 |
| 147 | Insertion Sort List | 中等 | P2 | 已做 | 插入排序 |
| 237 | Delete Node in a Linked List | 中等 | P2 | 已做 | 技巧题 |

### 二、数组、双指针、滑动窗口与哈希（array / two pointers / sliding window / hashing）

你的流式处理和监控指标经验（时间窗口、去重、聚合）经常以这类题的形式被考到。你做过 Sliding Window Maximum 和 Minimum Size Subarray Sum，但窗口类的其他变形和哈希题还没做。

本主题：26 题（新题 11，已做 15）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 1 | Two Sum | 简单 | P0 | 新题 | 哈希表基本功，热身 |
| 49 | Group Anagrams | 中等 | P0 | 新题 | 按特征分组；类似数据平台里按标签聚合 |
| 3 | Longest Substring Without Repeating Characters | 中等 | P0 | 新题 | 滑动窗口的标准模板 |
| 76 | Minimum Window Substring | 困难 | P0 | 新题 | 滑动窗口进阶：覆盖条件的收缩与扩张 |
| 560 | Subarray Sum Equals K | 中等 | P0 | 新题 | 前缀和（prefix sum）加哈希；时序指标聚合 |
| 128 | Longest Consecutive Sequence | 中等 | P0 | 新题 | 哈希集合做到线性时间；和乱序到达的序号处理思路接近 |
| 15 | 3Sum | 中等 | P0 | 新题 | 排序加双指针，去重细节 |
| 239 | Sliding Window Maximum | 困难 | P0 | 已做 | 单调队列（monotonic deque） |
| 238 | Product of Array Except Self | 中等 | P0 | 已做 | 前缀积与后缀积 |
| 11 | Container With Most Water | 中等 | P0 | 已做 | 双指针的证明思路 |
| 75 | Sort Colors | 中等 | P0 | 已做 | 三指针（荷兰国旗） |
| 424 | Longest Repeating Character Replacement | 中等 | P1 | 新题 | 滑动窗口加计数 |
| 567 | Permutation in String | 中等 | P1 | 新题 | 固定窗口加计数比较 |
| 41 | First Missing Positive | 困难 | P1 | 新题 | 原地哈希；在乱序数据里找缺口 |
| 42 | Trapping Rain Water | 困难 | P1 | 新题 | 双指针或单调栈两种解法对比 |
| 209 | Minimum Size Subarray Sum | 中等 | P1 | 已做 | 滑动窗口 |
| 167 | Two Sum II - Input Array Is Sorted | 中等 | P1 | 已做 | 双指针 |
| 242 | Valid Anagram | 简单 | P1 | 已做 | 计数 |
| 283 | Move Zeroes | 简单 | P1 | 已做 | 原地双指针 |
| 80 | Remove Duplicates from Sorted Array II | 中等 | P1 | 已做 | 原地处理，快慢指针 |
| 189 | Rotate Array | 中等 | P1 | 已做 | 三次反转 |
| 287 | Find the Duplicate Number | 中等 | P1 | 已做 | 快慢指针或二分 |
| 220 | Contains Duplicate III | 困难 | P2 | 已做 | 桶或有序窗口；滑动窗口内的近似去重 |
| 217 | Contains Duplicate | 简单 | P2 | 已做 | 热身 |
| 27 | Remove Element | 简单 | P2 | 已做 | 热身 |
| 59 | Spiral Matrix II | 中等 | P2 | 已做 | 矩阵模拟 |

### 三、栈与单调栈（stack / monotonic stack）

你做过 Valid Parentheses 和 Min Stack，但没有单调栈。单调栈是中等难度题里的高频考点。

本主题：9 题（新题 6，已做 3）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 739 | Daily Temperatures | 中等 | P0 | 新题 | 单调栈模板 |
| 20 | Valid Parentheses | 简单 | P0 | 已做 | 栈的入门题 |
| 155 | Min Stack | 中等 | P0 | 已做 | 辅助栈 |
| 901 | Online Stock Span | 中等 | P1 | 新题 | 在线（流式）单调栈 |
| 394 | Decode String | 中等 | P1 | 新题 | 栈加嵌套解析；类似配置解析 |
| 227 | Basic Calculator II | 中等 | P1 | 新题 | 表达式解析 |
| 84 | Largest Rectangle in Histogram | 困难 | P1 | 新题 | 单调栈进阶 |
| 224 | Basic Calculator | 困难 | P2 | 新题 | 带括号的表达式 |
| 225 | Implement Stack using Queues | 简单 | P2 | 已做 | 热身 |

### 四、二分查找（binary search）

你只做过搜索二维矩阵、插入位置和两个有序数组的中位数，缺少最常见的变形：旋转数组、在答案上二分、带时间戳的查询。

本主题：12 题（新题 8，已做 4）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 33 | Search in Rotated Sorted Array | 中等 | P0 | 新题 | 二分的经典变形 |
| 34 | Find First and Last Position of Element in Sorted Array | 中等 | P0 | 新题 | 左右边界二分 |
| 981 | Time Based Key-Value Store | 中等 | P0 | 新题 | 哈希加二分；带版本或时间戳的键值存储，和你做过的存储引擎、乱序更新相关 |
| 875 | Koko Eating Bananas | 中等 | P0 | 新题 | 在答案上二分（binary search on answer）；容量和限速类问题 |
| 153 | Find Minimum in Rotated Sorted Array | 中等 | P1 | 新题 | 旋转数组 |
| 1011 | Capacity To Ship Packages Within D Days | 中等 | P1 | 新题 | 在答案上二分；任务分配和容量规划 |
| 74 | Search a 2D Matrix | 中等 | P1 | 已做 | 把二维当一维做二分 |
| 240 | Search a 2D Matrix II | 中等 | P1 | 已做 | 从角落出发的线性搜索 |
| 4 | Median of Two Sorted Arrays | 困难 | P1 | 已做 | 二分的边界处理，是难题里的经典 |
| 162 | Find Peak Element | 中等 | P2 | 新题 | 二分的另一种思路 |
| 410 | Split Array Largest Sum | 困难 | P2 | 新题 | 在答案上二分的进阶 |
| 35 | Search Insert Position | 简单 | P2 | 已做 | 热身 |

### 五、堆与优先队列（heap / priority queue）

**这是你仓库里完全空白、但面试里最常出现的一类。** 对应你的简历：流式统计（在线学习）、调度、批处理、多路归并。

本主题：14 题（新题 14，已做 0）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 215 | Kth Largest Element in an Array | 中等 | P0 | 新题 | 堆或快速选择 |
| 347 | Top K Frequent Elements | 中等 | P0 | 新题 | 哈希加堆，或桶排序 |
| 23 | Merge k Sorted Lists | 困难 | P0 | 新题 | k 路归并；事件流和日志合并 |
| 295 | Find Median from Data Stream | 困难 | P0 | 新题 | 双堆；流式统计 |
| 621 | Task Scheduler | 中等 | P1 | 新题 | 贪心加堆；调度与批处理 |
| 355 | Design Twitter | 中等 | P1 | 新题 | k 路归并加设计；订阅和时间线，和你的订阅管理相关 |
| 703 | Kth Largest Element in a Stream | 简单 | P1 | 新题 | 流式 top-k |
| 973 | K Closest Points to Origin | 中等 | P1 | 新题 | 堆或快速选择 |
| 1834 | Single-Threaded CPU | 中等 | P1 | 新题 | 堆加事件模拟；任务调度 |
| 767 | Reorganize String | 中等 | P2 | 新题 | 贪心加堆 |
| 692 | Top K Frequent Words | 中等 | P2 | 新题 | 自定义排序的堆 |
| 378 | Kth Smallest Element in a Sorted Matrix | 中等 | P2 | 新题 | 堆或二分 |
| 480 | Sliding Window Median | 困难 | P2 | 新题 | 双堆加延迟删除 |
| 871 | Minimum Number of Refueling Stops | 困难 | P2 | 新题 | 贪心加堆 |

### 六、区间（intervals）

对应你的调度、批处理，以及乱序到达的序号区间。仓库里没有区间类的题。

本主题：10 题（新题 10，已做 0）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 56 | Merge Intervals | 中等 | P0 | 新题 | 区间题的基础 |
| 253 | Meeting Rooms II（会员） | 中等 | P0 | 新题 | 扫描线或堆；资源并发上限 |
| 57 | Insert Interval | 中等 | P1 | 新题 | 区间插入与合并 |
| 435 | Non-overlapping Intervals | 中等 | P1 | 新题 | 贪心 |
| 352 | Data Stream as Disjoint Intervals | 困难 | P1 | 新题 | 流式合并区间；类似维护已收到的序号区间，贴近你的乱序更新工作 |
| 986 | Interval List Intersections | 中等 | P2 | 新题 | 双指针 |
| 1094 | Car Pooling | 中等 | P2 | 新题 | 差分数组 |
| 1235 | Maximum Profit in Job Scheduling | 困难 | P2 | 新题 | 动态规划加二分；任务调度 |
| 732 | My Calendar III | 困难 | P2 | 新题 | 扫描线或线段树 |
| 218 | The Skyline Problem | 困难 | P2 | 新题 | 扫描线加堆 |

### 七、图（graph）：和你的工作最贴近的一类

你在做 CVaaS 的拓扑服务，面试官很可能顺着这个话题出图题，甚至直接问网络拓扑的场景。你只做过 Number of Islands 和 Course Schedule。重点补：拓扑排序（topological sort）、并查集（union-find）、最短路径（shortest path）、桥与割点（bridges / Tarjan）。

本主题：23 题（新题 20，已做 3）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 133 | Clone Graph | 中等 | P0 | 新题 | 图的遍历与拷贝 |
| 547 | Number of Provinces | 中等 | P0 | 新题 | 连通分量；并查集 |
| 210 | Course Schedule II | 中等 | P0 | 新题 | 拓扑排序，输出依赖顺序；部署与依赖编排 |
| 743 | Network Delay Time | 中等 | P0 | 新题 | Dijkstra 最短路径；网络延迟 |
| 1192 | Critical Connections in a Network | 困难 | P0 | 新题 | 桥（bridge）与 Tarjan 算法；网络拓扑里的关键链路，和你的工作最贴近 |
| 200 | Number of Islands | 中等 | P0 | 已做 | 再用并查集写一遍，和 DFS 对比 |
| 207 | Course Schedule | 中等 | P0 | 已做 | 再用 BFS（Kahn 算法）写一遍 |
| 684 | Redundant Connection | 中等 | P1 | 新题 | 并查集检测环 |
| 721 | Accounts Merge | 中等 | P1 | 新题 | 并查集进阶 |
| 310 | Minimum Height Trees | 中等 | P1 | 新题 | 拓扑剥离；找网络中心节点 |
| 787 | Cheapest Flights Within K Stops | 中等 | P1 | 新题 | Bellman-Ford 或分层 BFS |
| 127 | Word Ladder | 困难 | P1 | 新题 | BFS 最短路径 |
| 417 | Pacific Atlantic Water Flow | 中等 | P1 | 新题 | 多源搜索 |
| 994 | Rotting Oranges | 中等 | P1 | 新题 | 多源 BFS |
| 269 | Alien Dictionary（会员） | 困难 | P1 | 新题 | 拓扑排序的综合应用 |
| 1203 | Sort Items by Groups Respecting Dependencies | 困难 | P2 | 新题 | 两层拓扑排序；依赖编排，和你做的部署服务相关 |
| 1631 | Path With Minimum Effort | 中等 | P2 | 新题 | Dijkstra 或二分加搜索 |
| 399 | Evaluate Division | 中等 | P2 | 新题 | 带权图或带权并查集 |
| 785 | Is Graph Bipartite? | 中等 | P2 | 新题 | 图染色 |
| 130 | Surrounded Regions | 中等 | P2 | 新题 | 网格搜索 |
| 332 | Reconstruct Itinerary | 困难 | P2 | 新题 | 欧拉路径 |
| 1584 | Min Cost to Connect All Points | 中等 | P2 | 新题 | 最小生成树（MST） |
| 329 | Longest Increasing Path in a Matrix | 困难 | P2 | 已做 | 图上的记忆化搜索，也可以用拓扑排序 |

### 八、二叉树（binary tree）

你的树题以遍历、构造和二叉搜索树为主，缺少层序遍历、普通二叉树的最近公共祖先、路径和类。

本主题：24 题（新题 8，已做 16）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 102 | Binary Tree Level Order Traversal | 中等 | P0 | 新题 | 层序遍历是很多题的基础 |
| 98 | Validate Binary Search Tree | 中等 | P0 | 新题 | 区间约束的递归 |
| 236 | Lowest Common Ancestor of a Binary Tree | 中等 | P0 | 新题 | 普通二叉树的最近公共祖先 |
| 105 | Construct Binary Tree from Preorder and Inorder Traversal | 中等 | P0 | 已做 | 递归构造，面试高频 |
| 230 | Kth Smallest Element in a BST | 中等 | P0 | 已做 | 中序遍历 |
| 199 | Binary Tree Right Side View | 中等 | P1 | 新题 | 层序遍历的变形 |
| 543 | Diameter of Binary Tree | 简单 | P1 | 新题 | 递归返回多个信息 |
| 124 | Binary Tree Maximum Path Sum | 困难 | P1 | 新题 | 树形动态规划 |
| 297 | Serialize and Deserialize Binary Tree | 困难 | P1 | 新题 | 序列化；协议与存储 |
| 104 | Maximum Depth of Binary Tree | 简单 | P1 | 已做 | 热身 |
| 226 | Invert Binary Tree | 简单 | P1 | 已做 | 热身 |
| 100 | Same Tree | 简单 | P1 | 已做 | 热身 |
| 94 | Binary Tree Inorder Traversal | 简单 | P1 | 已做 | 迭代写法也要会 |
| 235 | Lowest Common Ancestor of a Binary Search Tree | 中等 | P1 | 已做 | 利用 BST 的性质 |
| 114 | Flatten Binary Tree to Linked List | 中等 | P1 | 已做 | 原地改造 |
| 129 | Sum Root to Leaf Numbers | 中等 | P1 | 已做 | 路径上的累积 |
| 572 | Subtree of Another Tree | 简单 | P2 | 新题 | 树的比较 |
| 144 | Binary Tree Preorder Traversal | 简单 | P2 | 已做 | 热身 |
| 108 | Convert Sorted Array to Binary Search Tree | 简单 | P2 | 已做 | 热身 |
| 116 | Populating Next Right Pointers in Each Node | 中等 | P2 | 已做 | 层序的变形 |
| 99 | Recover Binary Search Tree | 中等 | P2 | 已做 | 中序遍历找错位节点 |
| 95 | Unique Binary Search Trees II | 中等 | P2 | 已做 | 递归生成 |
| 96 | Unique Binary Search Trees | 中等 | P2 | 已做 | 卡特兰数的动态规划 |
| 331 | Verify Preorder Serialization of a Binary Tree | 中等 | P2 | 已做 | 出入度计数 |

### 九、回溯与字符串解析（backtracking）

你的回溯基础已经很扎实（N 皇后、数独、组合、排列都做过），主要是复习，再补几道没做过的，加上有网络背景的 IP 地址题。

本主题：18 题（新题 6，已做 12）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 78 | Subsets | 中等 | P0 | 新题 | 回溯的基础模板 |
| 79 | Word Search | 中等 | P0 | 新题 | 网格回溯 |
| 46 | Permutations | 中等 | P0 | 已做 | 回溯模板 |
| 39 | Combination Sum | 中等 | P0 | 已做 | 回溯加剪枝 |
| 22 | Generate Parentheses | 中等 | P0 | 已做 | 回溯，面试高频 |
| 131 | Palindrome Partitioning | 中等 | P1 | 新题 | 回溯加回文判断 |
| 17 | Letter Combinations of a Phone Number | 中等 | P1 | 新题 | 回溯 |
| 468 | Validate IP Address | 中等 | P1 | 新题 | 字符串解析；网络背景，容易出现在你的面试里 |
| 47 | Permutations II | 中等 | P1 | 已做 | 去重 |
| 40 | Combination Sum II | 中等 | P1 | 已做 | 去重 |
| 77 | Combinations | 中等 | P1 | 已做 | 回溯 |
| 90 | Subsets II | 中等 | P1 | 已做 | 去重 |
| 51 | N-Queens | 困难 | P1 | 已做 | 回溯的经典难题 |
| 93 | Restore IP Addresses | 中等 | P2 | 新题 | 回溯加 IP 规则 |
| 216 | Combination Sum III | 中等 | P2 | 已做 | 回溯 |
| 89 | Gray Code | 中等 | P2 | 已做 | 位运算或回溯 |
| 301 | Remove Invalid Parentheses | 困难 | P2 | 已做 | BFS 或回溯 |
| 37 | Sudoku Solver | 困难 | P2 | 已做 | 回溯加剪枝 |

### 十、动态规划与贪心（dynamic programming & greedy）

你的动态规划是强项（股票系列、编辑距离、戳气球、打家劫舍都做过），以复习为主。补几道高频的背包、子序列和字符串类，再加几道你没做过的贪心。

本主题：38 题（新题 18，已做 20）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 322 | Coin Change | 中等 | P0 | 新题 | 完全背包 |
| 139 | Word Break | 中等 | P0 | 新题 | 字符串切分；和查询改写、分词相关 |
| 1143 | Longest Common Subsequence | 中等 | P0 | 新题 | 二维动态规划的基础 |
| 70 | Climbing Stairs | 简单 | P0 | 已做 | 热身 |
| 198 | House Robber | 中等 | P0 | 已做 | 一维动态规划 |
| 62 | Unique Paths | 中等 | P0 | 已做 | 二维动态规划 |
| 72 | Edit Distance | 中等 | P0 | 已做 | 经典的二维动态规划；也和查询改写相关 |
| 300 | Longest Increasing Subsequence | 中等 | P0 | 已做 | 动态规划和二分两种解法 |
| 121 | Best Time to Buy and Sell Stock | 简单 | P0 | 已做 | 股票系列的起点 |
| 122 | Best Time to Buy and Sell Stock II | 中等 | P0 | 已做 | 贪心 |
| 55 | Jump Game | 中等 | P0 | 已做 | 贪心 |
| 416 | Partition Equal Subset Sum | 中等 | P1 | 新题 | 0-1 背包 |
| 5 | Longest Palindromic Substring | 中等 | P1 | 新题 | 中心扩展或动态规划 |
| 53 | Maximum Subarray | 中等 | P1 | 新题 | 一维动态规划 |
| 152 | Maximum Product Subarray | 中等 | P1 | 新题 | 维护最大最小两个状态 |
| 91 | Decode Ways | 中等 | P1 | 新题 | 计数型动态规划 |
| 221 | Maximal Square | 中等 | P1 | 新题 | 二维动态规划 |
| 45 | Jump Game II | 中等 | P1 | 新题 | 贪心 |
| 134 | Gas Station | 中等 | P1 | 新题 | 贪心 |
| 337 | House Robber III | 中等 | P1 | 已做 | 树形动态规划 |
| 64 | Minimum Path Sum | 中等 | P1 | 已做 | 二维动态规划 |
| 309 | Best Time to Buy and Sell Stock with Cooldown | 中等 | P1 | 已做 | 状态机动态规划 |
| 123 | Best Time to Buy and Sell Stock III | 困难 | P1 | 已做 | 状态机动态规划 |
| 188 | Best Time to Buy and Sell Stock IV | 困难 | P1 | 已做 | 状态机动态规划 |
| 312 | Burst Balloons | 困难 | P1 | 已做 | 区间动态规划 |
| 97 | Interleaving String | 中等 | P1 | 已做 | 二维动态规划 |
| 32 | Longest Valid Parentheses | 困难 | P1 | 已做 | 动态规划或栈 |
| 304 | Range Sum Query 2D - Immutable | 中等 | P1 | 已做 | 二维前缀和 |
| 140 | Word Break II | 困难 | P2 | 新题 | 记忆化搜索 |
| 518 | Coin Change II | 中等 | P2 | 新题 | 组合数背包 |
| 494 | Target Sum | 中等 | P2 | 新题 | 背包的转化 |
| 647 | Palindromic Substrings | 中等 | P2 | 新题 | 回文计数 |
| 354 | Russian Doll Envelopes | 困难 | P2 | 新题 | 最长递增子序列加二分 |
| 10 | Regular Expression Matching | 困难 | P2 | 新题 | 二维动态规划的难题 |
| 763 | Partition Labels | 中等 | P2 | 新题 | 贪心 |
| 115 | Distinct Subsequences | 困难 | P2 | 已做 | 二维动态规划 |
| 87 | Scramble String | 困难 | P2 | 已做 | 区间动态规划或记忆化搜索 |
| 343 | Integer Break | 中等 | P2 | 已做 | 动态规划或数学 |

### 十一、前缀树与字符串（trie）：对应你的查询改写经历

你在阿里做过广告搜索的查询改写，这一类是最自然的话题。仓库里完全没有前缀树。

本主题：8 题（新题 8，已做 0）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 208 | Implement Trie (Prefix Tree) | 中等 | P0 | 新题 | 前缀树基础；查询改写和自动补全 |
| 211 | Design Add and Search Words Data Structure | 中等 | P1 | 新题 | 带通配符的前缀树 |
| 648 | Replace Words | 中等 | P1 | 新题 | 前缀替换；就是一种简单的查询改写 |
| 1268 | Search Suggestions System | 中等 | P1 | 新题 | 自动补全 |
| 212 | Word Search II | 困难 | P1 | 新题 | 前缀树加回溯 |
| 642 | Design Search Autocomplete System（会员） | 困难 | P1 | 新题 | 自动补全的设计题 |
| 1032 | Stream of Characters | 困难 | P2 | 新题 | 流式输入加多模式匹配 |
| 336 | Palindrome Pairs | 困难 | P2 | 新题 | 前缀树或哈希 |

### 十二、设计题（design）：对应你的存储、订阅、乱序更新、监控经历

这一类最能把你的简历经历接上算法题。你只做过 LRU Cache、Min Stack 和 BST Iterator。**带星号的几道（Stock Price Fluctuation、Design an Ordered Stream）和你的乱序更新过滤最贴近。**

本主题：25 题（新题 23，已做 2）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 2034 | Stock Price Fluctuation | 中等 | P0 | 新题 | ★ 数据乱序到达，后到的更正会覆盖旧值；哈希加双堆加延迟删除。和你的乱序更新过滤最贴近 |
| 1656 | Design an Ordered Stream | 简单 | P0 | 新题 | ★ 乱序到达、按序释放；同样很贴近 |
| 460 | LFU Cache | 困难 | P0 | 新题 | 哈希加双向链表；缓存淘汰，LRU 的进阶 |
| 380 | Insert Delete GetRandom O(1) | 中等 | P0 | 新题 | 哈希加数组 |
| 146 | LRU Cache | 中等 | P0 | 已做 | 限时 20 分钟，各用手写链表和 OrderedDict 写一遍 |
| 622 | Design Circular Queue | 中等 | P1 | 新题 | 环形缓冲区（ring buffer）；传输层和流控，和你的 Go 传输库相关 |
| 706 | Design HashMap | 简单 | P1 | 新题 | 存储引擎基础 |
| 1146 | Snapshot Array | 中等 | P1 | 新题 | 版本化存储 |
| 1348 | Tweet Counts Per Frequency | 中等 | P1 | 新题 | 时间窗口聚合；监控指标，和你在 AWS 做的指标服务相关 |
| 933 | Number of Recent Calls | 简单 | P1 | 新题 | 滑动时间窗口；限流 |
| 362 | Design Hit Counter（会员） | 中等 | P1 | 新题 | 时间窗口计数；限流 |
| 359 | Logger Rate Limiter（会员） | 简单 | P1 | 新题 | 限流 |
| 173 | Binary Search Tree Iterator | 中等 | P1 | 已做 | 迭代器设计，受控遍历 |
| 432 | All O(1) Data Structure | 困难 | P2 | 新题 | 哈希加双向链表 |
| 1206 | Design Skiplist | 困难 | P2 | 新题 | 跳表；存储引擎，和你做过的 NTSE 相关 |
| 1396 | Design Underground System | 中等 | P2 | 新题 | 哈希聚合 |
| 715 | Range Module | 困难 | P2 | 新题 | 区间管理 |
| 307 | Range Sum Query - Mutable | 中等 | P2 | 新题 | 树状数组或线段树 |
| 895 | Maximum Frequency Stack | 困难 | P2 | 新题 | 分桶栈 |
| 1352 | Product of the Last K Numbers | 中等 | P2 | 新题 | 前缀积 |
| 1825 | Finding MK Average | 困难 | P2 | 新题 | 数据流统计 |
| 588 | Design In-Memory File System（会员） | 困难 | P2 | 新题 | 前缀树和哈希 |
| 635 | Design Log Storage System（会员） | 中等 | P2 | 新题 | 日志按时间范围查询 |
| 284 | Peeking Iterator | 中等 | P2 | 新题 | 迭代器设计 |
| 341 | Flatten Nested List Iterator | 中等 | P2 | 新题 | 迭代器设计 |

### 十三、随机与采样（sampling）：对应你做过的广告和在线服务

你做过 Linked List Random Node（蓄水池抽样，reservoir sampling），再补几道相关的。

本主题：4 题（新题 3，已做 1）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 528 | Random Pick with Weight | 中等 | P1 | 新题 | 按权重采样；广告与在线服务 |
| 382 | Linked List Random Node | 中等 | P1 | 已做 | 蓄水池抽样 |
| 398 | Random Pick Index | 中等 | P2 | 新题 | 蓄水池抽样 |
| 470 | Implement Rand10() Using Rand7() | 中等 | P2 | 新题 | 拒绝采样 |

### 十四、并发（concurrency）：对应你的 Go 传输库和并发经验

LeetCode 有一组专门的并发题。大厂的算法轮里很少考，但你的简历写了并发，系统轮和后端岗位的追问可能涉及。**这些题所支持的语言以站点当前显示为准。**

本主题：9 题（新题 9，已做 0）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 1114 | Print in Order | 简单 | P1 | 新题 | 线程同步基础 |
| 1115 | Print FooBar Alternately | 中等 | P1 | 新题 | 两线程交替 |
| 1226 | The Dining Philosophers | 中等 | P1 | 新题 | 死锁与资源顺序 |
| 1188 | Design Bounded Blocking Queue（会员） | 中等 | P1 | 新题 | 生产者消费者；有界阻塞队列 |
| 1116 | Print Zero Even Odd | 中等 | P2 | 新题 | 三线程协调 |
| 1117 | Building H2O | 中等 | P2 | 新题 | 屏障（barrier） |
| 1195 | Fizz Buzz Multithreaded | 中等 | P2 | 新题 | 四线程协调 |
| 1242 | Web Crawler Multithreaded（会员） | 中等 | P2 | 新题 | 并发爬取与去重 |
| 1279 | Traffic Light Controlled Intersection（会员） | 简单 | P2 | 新题 | 互斥与状态 |

### 十五、SQL：简历技能里写了 SQL，部分公司的电话面或笔试会考

仓库里没有 SQL 题。以下都是高频题，做一遍就够。

本主题：11 题（新题 11，已做 0）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 175 | Combine Two Tables | 简单 | P1 | 新题 | 连接（JOIN） |
| 176 | Second Highest Salary | 中等 | P1 | 新题 | 排序与子查询 |
| 180 | Consecutive Numbers | 中等 | P1 | 新题 | 窗口函数 |
| 185 | Department Top Three Salaries | 困难 | P1 | 新题 | 分组内排名 |
| 177 | Nth Highest Salary | 中等 | P2 | 新题 | 排名函数 |
| 178 | Rank Scores | 中等 | P2 | 新题 | 窗口函数 |
| 262 | Trips and Users | 困难 | P2 | 新题 | 复杂的连接和聚合 |
| 601 | Human Traffic of Stadium | 困难 | P2 | 新题 | 连续区间 |
| 1321 | Restaurant Growth | 中等 | P2 | 新题 | 滑动窗口聚合 |
| 197 | Rising Temperature | 简单 | P2 | 新题 | 自连接 |
| 550 | Game Play Analysis IV | 中等 | P2 | 新题 | 留存率计算 |

### 十六、基础、位运算与数学（你已经做过大部分，快速过一遍即可）

这部分你做得很多，不需要花时间深挖。每道题能在几分钟内写出来就算过关。另补了几道面试里常见的数学与字符串转换题（Reverse Integer、atoi、Pow(x, n)、Sqrt(x)）。

本主题：29 题（新题 4，已做 25）。

| 题号 | 题名 | 难度 | 优先级 | 状态 | 考点与为什么适合你 |
|---|---|---|---|---|---|
| 7 | Reverse Integer | 中等 | P1 | 新题 | 溢出处理 |
| 8 | String to Integer (atoi) | 中等 | P1 | 新题 | 字符串解析和边界 |
| 50 | Pow(x, n) | 中等 | P1 | 新题 | 快速幂 |
| 69 | Sqrt(x) | 简单 | P1 | 新题 | 二分 |
| 136 | Single Number | 简单 | P1 | 已做 | 异或 |
| 191 | Number of 1 Bits | 简单 | P1 | 已做 | 位运算 |
| 137 | Single Number II | 中等 | P2 | 已做 | 位计数 |
| 260 | Single Number III | 中等 | P2 | 已做 | 异或分组 |
| 338 | Counting Bits | 简单 | P2 | 已做 | 动态规划与位运算 |
| 231 | Power of Two | 简单 | P2 | 已做 | 位运算 |
| 371 | Sum of Two Integers | 中等 | P2 | 已做 | 位运算做加法 |
| 268 | Missing Number | 简单 | P2 | 已做 | 异或或求和 |
| 169 | Majority Element | 简单 | P2 | 已做 | 摩尔投票 |
| 263 | Ugly Number | 简单 | P2 | 已做 | 数学 |
| 264 | Ugly Number II | 中等 | P2 | 已做 | 堆或三指针 |
| 313 | Super Ugly Number | 中等 | P2 | 已做 | 堆或多指针 |
| 318 | Maximum Product of Word Lengths | 中等 | P2 | 已做 | 位掩码 |
| 319 | Bulb Switcher | 中等 | P2 | 已做 | 数学 |
| 292 | Nim Game | 简单 | P2 | 已做 | 数学 |
| 441 | Arranging Coins | 简单 | P2 | 已做 | 数学或二分 |
| 258 | Add Digits | 简单 | P2 | 已做 | 数学 |
| 9 | Palindrome Number | 简单 | P2 | 已做 | 热身 |
| 13 | Roman to Integer | 简单 | P2 | 已做 | 热身 |
| 14 | Longest Common Prefix | 简单 | P2 | 已做 | 热身 |
| 58 | Length of Last Word | 简单 | P2 | 已做 | 热身 |
| 66 | Plus One | 简单 | P2 | 已做 | 热身 |
| 171 | Excel Sheet Column Number | 简单 | P2 | 已做 | 热身 |
| 344 | Reverse String | 简单 | P2 | 已做 | 热身 |
| 345 | Reverse Vowels of a String | 简单 | P2 | 已做 | 热身 |

## 学习计划

### 已做的题怎么复习（省事的做法）

1. **闭卷重写**：不看你仓库里的旧代码，直接在白板或编辑器里用 Python 3 重写。
2. **限时判断**：简单题 10 分钟，中等题 20 分钟，困难题 35 分钟。**一次写对且在时限内的，标记为"掌握"，以后不用再碰**；写不出或写错的，才看旧代码，再隔天重做一次。
3. **不要只看答案**：看到旧代码觉得"我会"不等于会写。面试里没有人给你旧代码。
4. **复习的重点是能讲清楚**：为什么这样做、复杂度是多少、边界情况有哪些。

### 方案一：四周冲刺（面试在一个月内）

只做 **P0**：新题 38 道、复习 25 道。已做的题每道限时几分钟，新题每天 2 到 3 道，周末做一次限时模拟。

| 周 | 主题 | P0 新题 | P0 复习 |
|---|---|---|---|
| 第 1 周 | 一、链表；二、数组、双指针、滑动窗口与哈希；三、栈与单调栈；四、二分查找 | 14 | 9 |
| 第 2 周 | 五、堆与优先队列；六、区间；八、二叉树 | 9 | 2 |
| 第 3 周 | 七、图；十二、设计题 | 9 | 3 |
| 第 4 周 | 九、回溯与字符串解析；十、动态规划与贪心；十一、前缀树与字符串；十六、基础、位运算与数学；十三、随机与采样 | 6 | 11 |

### 方案二：八周稳扎稳打

做 **P0 加 P1**：新题 105 道、复习 68 道，每周约 13 道新题加若干复习，最后一周做模拟面试和错题回顾。P2 作为选做。

| 周 | 主题 |
|---|---|
| 第 1 周 | 链表（复习为主）、数组、滑动窗口与哈希、栈 |
| 第 2 周 | 二分查找、堆 |
| 第 3 周 | 区间、二叉树 |
| 第 4 周 | 图（上）：遍历、拓扑排序、并查集 |
| 第 5 周 | 图（下）：最短路径、桥与割点；回溯补充 |
| 第 6 周 | 设计题、采样 |
| 第 7 周 | 前缀树、动态规划（复习为主）、SQL、并发 |
| 第 8 周 | 限时模拟、错题复盘、把简历故事和算法题接起来 |

### 每道新题怎么练

- **限时**：每道中等题给自己 25 到 30 分钟。想不出来就看题解，**然后关掉题解自己重写一遍**。
- **间隔复习**：做过的新题在 1 天后、3 天后、1 周后各再做一次，只做做错或做得慢的。
- **边说边写**：资深面试看沟通。练习时大声讲：先复述题意，问边界条件，给出暴力解法再优化，说明时间和空间复杂度，写完用例子走一遍。
- **追问要提前准备**：很多题面试官会追问"数据量大到放不进内存怎么办""多台机器怎么扩展""流式输入怎么办"。你的简历在这方面有真实经验，要把它讲出来。
- **模板化**：把堆、并查集、拓扑排序、Dijkstra、前缀树、二分的模板各自写熟，面试时少犯低级错误。
- **不要在做题时开着 AI**：我前面的调研里，多数公司的现场算法轮默认关闭 AI（单一来源的说法，请向招聘人员确认）；有的公司（据报道，如 Meta）有"AI 辅助编程轮"，那一轮考的是读懂已有代码、驱动 AI、验证结果，可以另外练习，而你简历里写的 AI 辅助开发经验在那种轮次里是优势。

## 从简历故事到算法讲法

下面几个例子，是把简历里的经历转成面试里的算法讨论。**这些是通用的思路，不代表你实际做的设计**，你要按自己真实做过的版本来讲。

### 乱序更新过滤，限制内存增长

面试官可能问："每条更新有序号或时间戳，会乱序、重复、迟到，怎么过滤，同时内存有上限？" 可以从这些积木里组合：

- 每个键只保存**已应用的最大版本**（高水位），比它旧的直接丢弃（类似 Stock Price Fluctuation 里"后到的更正覆盖旧值"）。
- 如果需要保留"空洞"（序号 5 先到，3 和 4 还没到），用**滑动窗口加位图**或**有序缓冲**，窗口外的视为过期（类似网络里的重放窗口，也类似 Design an Ordered Stream 和 Data Stream as Disjoint Intervals）。
- 内存有界：窗口大小有上限，水位推进时回收；用堆或有序结构按序号淘汰（可参考 LFU Cache、Sliding Window Median 里的延迟删除思路）。
- 要说清取舍：窗口太小会误丢合法的迟到更新，太大则内存增长。

### 订阅管理器

面试官可能问："多个订阅者订阅同一个数据源，怎么只保持一个上游连接？" 思路是**引用计数加哈希**：键是订阅的数据路径，值是订阅者集合和上游句柄；第一个订阅者建立连接，最后一个取消时关闭。可以对照 LFU Cache、All O(1) Data Structure、Design Twitter（订阅关系加合并）。

### 事件更新改为批量更新

思路是**合并（coalescing）**：同一个键在一个批次内只保留最新值，到时间或达到数量就刷新。对照 Task Scheduler、Meeting Rooms II、Design Hit Counter。要说清楚用批量换来的是更低的计算量，代价是更新延迟，你的简历里已经有"数据延迟保持在几秒内"这个量化结果。

### 拓扑服务

连通性用并查集或 BFS；关键链路用桥（Tarjan，Critical Connections in a Network）；最短路径用 Dijkstra（Network Delay Time）；依赖顺序用拓扑排序（Course Schedule II）。如果面试官问"拓扑变化频繁怎么办"，可以讨论增量更新和并查集的局限（删除边困难）。

## 使用提醒

- 题号和难度来自我的记忆，请以 LeetCode 上的实际显示为准。
- 会员题我都标出来了。没有订阅的话，可以先跳过，或者用同主题的免费题替代（比如用 Car Pooling 和 Merge Intervals 代替 Meeting Rooms II）。
- "已做"是我根据你仓库的文件名判断的，我没有看过每道题的解答质量。如果你觉得某些已做的题其实掌握不牢，直接按"新题"的方式重做即可。
- 并发题在不同语言下是否可用，以 LeetCode 当前的显示为准。

