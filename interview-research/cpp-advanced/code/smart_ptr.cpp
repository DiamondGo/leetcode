// 实验 7：智能指针的真实开销与陷阱（libstdc++ / x86-64）。
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <memory>
#include <new>

static int g_allocs = 0;
void* operator new(std::size_t n) { ++g_allocs; if (void* p = std::malloc(n)) return p; throw std::bad_alloc(); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct Widget { int v[4]; Widget() { ++live; } ~Widget() { --live; } static inline int live = 0; };
struct Node { std::shared_ptr<Node> next; ~Node() { ++dead; } static inline int dead = 0; };
struct WNode { std::weak_ptr<WNode> next; ~WNode() { ++dead; } static inline int dead = 0; };
struct Session : std::enable_shared_from_this<Session> { std::shared_ptr<Session> self() { return shared_from_this(); } };

int main() {
  std::puts("== 大小 ==");
  auto lam = [](Widget* p) { delete p; };
  std::printf("sizeof(Widget*)=%zu  unique_ptr<W>=%zu  unique_ptr<W,无捕获lambda>=%zu  unique_ptr<W,函数指针>=%zu  unique_ptr<W,std::function>=%zu\n",
              sizeof(Widget*), sizeof(std::unique_ptr<Widget>), sizeof(std::unique_ptr<Widget, decltype(lam)>),
              sizeof(std::unique_ptr<Widget, void (*)(Widget*)>), sizeof(std::unique_ptr<Widget, std::function<void(Widget*)>>));
  std::printf("shared_ptr<W>=%zu  weak_ptr<W>=%zu （一个指向对象，一个指向控制块）\n", sizeof(std::shared_ptr<Widget>), sizeof(std::weak_ptr<Widget>));

  std::puts("== 分配次数 ==");
  g_allocs = 0; { std::shared_ptr<Widget> a(new Widget); }          std::printf("shared_ptr<W>(new W)      : %d 次堆分配\n", g_allocs);
  g_allocs = 0; { auto b = std::make_shared<Widget>(); }            std::printf("make_shared<W>()          : %d 次堆分配（对象和控制块一起）\n", g_allocs);
  g_allocs = 0; { auto c = std::make_unique<Widget>(); }            std::printf("make_unique<W>()          : %d 次堆分配\n", g_allocs);

  std::puts("== 循环引用泄漏 ==");
  { auto a = std::make_shared<Node>(); auto b = std::make_shared<Node>(); a->next = b; b->next = a; }
  std::printf("shared_ptr 成环：两个 Node 离开作用域后析构了 %d 个（泄漏）\n", Node::dead);
  { auto a = std::make_shared<WNode>(); auto b = std::make_shared<WNode>(); a->next = b; b->next = a; }
  std::printf("一边改成 weak_ptr：析构了 %d 个（正常）\n", WNode::dead);

  std::puts("== make_shared 与 weak_ptr：内存什么时候真正释放 ==");
  { std::weak_ptr<Widget> w; { auto s = std::make_shared<Widget>(); w = s; }
    std::printf("最后一个 shared_ptr 销毁后，对象已析构(live=%d)。注意：make_shared 把对象和控制块放在同一块内存里，只要还有 weak_ptr，这块内存就不归还（这一点这里没有测量，是实现行为）\n", Widget::live); }

  std::puts("== 别名构造 ==");
  { auto w = std::make_shared<Widget>(); std::shared_ptr<int> inner(w, &w->v[2]);
    std::printf("通过 shared_ptr<int> 指向成员，却共享 Widget 的控制块：use_count=%ld\n", w.use_count()); }

  std::puts("== enable_shared_from_this 误用 ==");
  try { Session s; auto p = s.self(); } catch (const std::bad_weak_ptr& e) { std::printf("栈对象上调用 shared_from_this：抛出 bad_weak_ptr（%s）\n", e.what()); }
  { auto s = std::make_shared<Session>(); auto p = s->self(); std::printf("由 make_shared 创建的对象：use_count=%ld\n", s.use_count()); }

}
