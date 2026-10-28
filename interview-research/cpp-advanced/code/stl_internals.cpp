// 实验 8：标准库容器的内部行为（libstdc++ 13，x86-64）。具体数字是实现细节，标准只规定复杂度。
#include <cstdio>
#include <deque>
#include <list>
#include <map>
#include <string>
#include <unordered_map>
#include <vector>

int main() {
  std::puts("== vector 的容量增长 ==");
  { std::vector<int> v; size_t last = 0; std::printf("容量序列：");
    for (int i = 0; i < 1000; ++i) { v.push_back(i); if (v.capacity() != last) { last = v.capacity(); std::printf("%zu ", last); } }
    std::puts("（libstdc++ 为 2 倍增长；MSVC 据说约 1.5 倍，这里没有验证）"); }
  { std::vector<int> v{1, 2, 3}; v.reserve(100); int* before = v.data(); v.shrink_to_fit();
    std::printf("shrink_to_fit 后地址%s变化（只是请求，不保证）\n", v.data() == before ? "没有" : "发生了"); }

  std::puts("== 迭代器/指针失效 ==");
  { std::vector<int> v{1, 2, 3}; v.reserve(3); int* p = &v[0]; v.push_back(4);
    std::printf("push_back 触发扩容后，旧指针 %s 新数据地址\n", p == &v[0] ? "仍等于" : "不再等于"); }
  { std::list<int> l{1, 2, 3}; auto it = l.begin(); l.push_back(4); l.push_front(0); std::printf("list 插入不使已有迭代器失效，*it=%d\n", *it); }
  { std::deque<int> d{1, 2, 3}; int* p = &d[1]; d.push_back(4); d.push_front(0); std::printf("deque 两端插入：旧元素的引用仍有效 *p=%d（但迭代器会失效）\n", *p); }

  std::puts("== std::string 的小字符串优化（SSO）==");
  { std::string s; std::printf("sizeof(string)=%zu  空串 capacity=%zu\n", sizeof(s), s.capacity());
    const char* base = s.data();
    for (int n = 1; n <= 20; ++n) { s.assign(n, 'x'); bool inl = s.data() >= (const char*)&s && s.data() < (const char*)(&s + 1);
      if (!inl) { std::printf("长度 %d 开始使用堆内存（SSO 能放下 %d 个字符 + 结尾 '\\0'）\n", n, n - 1); break; } } (void)base; }

  std::puts("== unordered_map 的桶与重哈希 ==");
  { std::unordered_map<int, int> m; size_t last = 0; std::printf("max_load_factor=%.1f；桶数增长：", m.max_load_factor());
    for (int i = 0; i < 2000; ++i) { m[i] = i; if (m.bucket_count() != last) { last = m.bucket_count(); std::printf("%zu(@%d) ", last, i); } }
    std::puts("");
    std::unordered_map<int, int> m2; m2.reserve(1000); std::printf("reserve(1000) 之后桶数=%zu，插入 1000 个元素不再重哈希\n", m2.bucket_count()); }
  { std::unordered_map<int, int> m{{1, 1}}; auto* p = &m[1]; for (int i = 2; i < 200; ++i) m[i] = i;
    std::printf("重哈希后，元素的引用仍有效（节点式存储）：*p=%d；但迭代器会失效\n", *p); }

  std::puts("== 节点式容器的元素开销（估算）==");
  std::printf("sizeof(std::pair<const int,int>)=%zu；map/unordered_map 每个节点还有指针、颜色或哈希缓存等簿记，实际每个元素远大于 8 字节\n", sizeof(std::pair<const int, int>));
}
