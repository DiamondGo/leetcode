# 高级 C++ 面试：原理、陷阱与深度问答

> **这份材料的来源与可信度**
>
> - 我先搜索了 C++ 面试题合集和高频交易（HFT）类公司的 C++ 面试内容：[Hyring：Top 60 C++ Interview Questions (2026)](https://hyring.com/jobseeker-toolkit/interview-questions/technical/cpp)、[TechPrep：128 C++ Interview Questions](https://www.techprep.app/blog/cpp-interview-questions)、[techinterview.org：C++ for Quants（HFT 与低延迟公司考什么）](https://www.techinterview.org/post/3233474597/cpp-quant-interviews/)、[techinterview.org：无锁队列问题](https://www.techinterview.org/post/3233476386/lock-free-queue-hft-interview-question/)、[quantvault：低延迟 C++ 面试题](https://quantvault.org/cpp-low-latency-interview-questions.html)。这些多是备考站的二手内容，**没有可核实的具体公司、具体年份的面经**，所以我只用它们确认“哪些主题常考”（内存模型、无锁、伪共享、未定义行为、模板、移动语义、STL 内部）。
> - **本材料里的每一个实验都在真实的编译器上编译并运行过**（g++ 13.3 与 clang++ 18.1，x86-64 Linux，4 核），输出原样贴在正文里；涉及并发的实验还用 ThreadSanitizer、AddressSanitizer、UndefinedBehaviorSanitizer 检查过。耗时数字取决于机器，只看相对大小；并发实验里的计数每次运行都不同。
> - 我的知识截止到 2026 年中。**C++26 的内容（反射、契约、hazard pointer 等）我没有用编译器验证，也没有对照最终标准文本**，凡是涉及 C++26 的地方都标了“未验证”。编译器对 C++20/23 特性的支持程度（模块、`std::print` 等）因版本而异，以你使用的编译器为准。
> - 正文里的“标准怎么规定”和“实现通常怎么做”是两回事，我尽量分开写：前者可以对着标准验证，后者（vptr 位置、`std::string` 的 SSO 容量、扩容倍数）是 libstdc++/Itanium ABI 的实现细节，**面试时要说明这是实现细节**。
> - 术语在每个小节第一次出现时附英文原名，附录有中英术语表。

## 零、高级 C++ 面试到底在考什么

初级 C++ 面试考语法（指针和引用的区别、`virtual` 是什么）。高级面试考的是**你能不能预测一段代码在机器上到底发生了什么**，并且**知道哪些东西语言保证、哪些东西只是碰巧如此**。常见的考察方式：

1. **机制题**：虚函数（virtual function）调用在汇编层面是什么样的？`shared_ptr` 的控制块（control block）里有什么？`std::move` 到底做了什么？
2. **陷阱题**：给你一段看起来没问题的代码，问输出或问哪里有未定义行为（UB, undefined behavior）。
3. **推理题**：这个无锁（lock-free）队列为什么需要 acquire/release？把它改成 relaxed 会怎样？
4. **手写题**：手写 `shared_ptr`、线程池（thread pool）、SPSC 队列、`std::function`、内存池（memory pool）。
5. **性能题**：这段代码为什么慢？缓存（cache）、分支预测（branch prediction）、伪共享（false sharing）、内存分配、虚调用能不能内联（inlining）？
6. **工程题**：线上 core dump 怎么分析？ABI 不兼容怎么排查？编译时间太长怎么办？

**不同类型的公司侧重不同**（据备考站的说法，具体因团队而异）：
- **高频交易与低延迟公司**：内存模型（memory model）、无锁数据结构、伪共享与缓存、避免堆分配、未定义行为、模板元编程。
- **大型互联网与基础设施公司**：并发（concurrency）正确性、智能指针（smart pointer）与所有权设计、STL 内部、构建与 ABI、性能剖析。
- **嵌入式与游戏**：内存布局、自定义分配器（allocator）、避免异常与 RTTI、数据导向设计（data-oriented design）。

**怎么用这份材料**：每章先读“为什么”和机制，运行或阅读实验，再看面试题。答案要点写得比较完整，但面试时请用自己的话说，并且尽量引用你自己项目里的例子。

**怎么运行实验**（需要 g++ 13+ 或 clang++ 17+）：

```text
cd interview-research/cpp-advanced/code
./run_all.sh            # 全部运行
./run_all.sh layout     # 只运行一个，名字见脚本里的 exp_ 函数
```

---

## 一、对象模型与内存布局

### 1.1 为什么要懂对象布局

C++ 的“零开销抽象”承诺的是：**你不用的东西不付费，你用的东西手写也不会更快。** 要兑现这个承诺，你得知道一个类到底占多少字节、成员在哪、虚函数（virtual function）怎么调用。知道了这些，你才能解释为什么两个“一样”的结构体大小不同、为什么多重继承（multiple inheritance）时指针值会变、为什么构造函数里调虚函数不会多态（polymorphism）。

### 1.2 对齐与填充

- 每种类型有**对齐要求**（`alignof`）：地址必须是它的整数倍。结构体的对齐是成员中最大的对齐；`sizeof` 一定是对齐的整数倍（这样数组里每个元素都对齐）。
- 编译器按**声明顺序**排列成员（标准保证同一访问控制段内后声明的地址更大），在需要的地方插入**填充（padding）**。所以成员顺序影响大小；按对齐从大到小排列通常最省。
- 对齐的原因：硬件按对齐的块访问内存更快（或根本不允许未对齐访问），并且保证一个对象不会横跨两个缓存行（cache line）或两个页。
- `alignas(64)` 可以提高对齐，常用于让对象独占缓存行（见第五章的伪共享（false sharing））。C++17 起 `operator new` 有对齐版本，可以正确分配过度对齐（over-aligned）的类型。

### 1.3 空基类优化与 `[[no_unique_address]]`

空类的大小至少是 1（保证不同对象有不同地址）。但**作为基类时，空基类可以不占空间**（空基类优化，EBO），这就是 `std::unique_ptr` 能和裸指针一样大的原因：删除器（deleter）是空类，作为基类“免费”存放。C++20 的 `[[no_unique_address]]` 让**成员**也能享受同样的待遇。

### 1.4 虚函数：vptr 与 vtable

标准只规定虚函数（virtual function）的**行为**，没有规定怎么实现。在 Linux/macOS 上 GCC 和 Clang 遵循 **Itanium C++ ABI**：

- 有虚函数的类，每个对象开头有一个隐藏指针 **vptr**，指向该类的 **vtable**（每个类一份，不是每个对象一份）。
- vtable 里有：到对象顶部的偏移（`offset-to-top`）、RTTI（`typeinfo`）指针、虚函数指针数组。
- 一次虚调用：读对象的 vptr → 读 vtable 里的槽位 → 间接调用。成本主要不是这两次读（通常在缓存（cache）里），而是**间接分支可能预测失败**，以及**编译器无法内联（inlining）**。
- **多重继承（multiple inheritance）**：每个带虚函数的基类子对象有自己的 vptr。把 `C*` 转成第二个基类 `B*` 时，指针值要加上偏移——`B*` 指向的是 C 对象内部的 B 子对象。通过 `B*` 调用在 C 里被重写的函数时，vtable 里放的是一个“**thunk**”，先把 `this` 调整回 `C*` 再跳转。
- **虚继承（virtual inheritance）**：为了让菱形继承里的虚基类只有一份，对象里存着虚基类的偏移（在 vtable 里），访问虚基类的成员要多一次间接寻址。
- **构造期间的动态类型**：基类构造函数运行时，对象的动态类型是基类，vptr 指向基类的 vtable；派生类构造函数开始时才改写 vptr。所以**在构造/析构函数里调用虚函数不会多态（polymorphism）**，只会调到当前正在构造的那一层，如果是纯虚函数则是未定义行为（UB, undefined behavior，通常崩溃）。

### 1.5 实验 1：看一看真实的布局

```cpp
// 实验 1：对象布局。关于 vptr、this 调整的观察依赖 Itanium C++ ABI（Linux/macOS 上的 GCC/Clang），
// 标准并不规定这些；MSVC 的布局不同。
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>

struct Bad  { char a; double b; char c; int d; };      // 填充很多
struct Good { double b; int d; char a; char c; };      // 同样的成员，按对齐从大到小
struct Empty {};
struct WithEmptyMember { Empty e; int x; };
struct WithNoUnique { [[no_unique_address]] Empty e; int x; };
struct alignas(64) Cache { int x; };

struct V0 { int x; };
struct V1 { virtual void f() {} int x; };
struct A { virtual void fa() {} int a = 1; };
struct B { virtual void fb() {} int b = 2; };
struct C : A, B { int c = 3; void fa() override {} void fb() override {} };
struct VB { int vb = 7; };
struct D1 : virtual VB { int d1; };
struct D2 : virtual VB { int d2; };
struct E : D1, D2 { int e; };
struct Base1 { int x = 0; virtual ~Base1() = default; virtual void who() {} };
struct Der1 : Base1 { int y = 0; void who() override {} };
struct Der2 : Base1 { void who() override {} };

static std::uintptr_t vptr_of(const void* obj) { std::uintptr_t p; std::memcpy(&p, obj, sizeof p); return p; }

int main() {
  std::printf("== 填充与重排 ==\n");
  std::printf("Bad{char,double,char,int}  sizeof=%zu\n", sizeof(Bad));
  std::printf("Good{double,int,char,char} sizeof=%zu\n", sizeof(Good));
  std::printf("offsetof(Bad,b)=%zu offsetof(Bad,c)=%zu offsetof(Bad,d)=%zu\n", offsetof(Bad, b), offsetof(Bad, c), offsetof(Bad, d));
  std::printf("== 空类 ==\n");
  std::printf("sizeof(Empty)=%zu  成员为 Empty: %zu  [[no_unique_address]]: %zu\n", sizeof(Empty), sizeof(WithEmptyMember), sizeof(WithNoUnique));
  std::printf("alignas(64) struct: sizeof=%zu alignof=%zu\n", sizeof(Cache), alignof(Cache));
  std::printf("== 虚函数与继承 ==\n");
  std::printf("sizeof(V0)=%zu  sizeof(V1 有虚函数)=%zu  (8 字节 vptr + 4 字节 int + 4 字节对齐填充)\n", sizeof(V0), sizeof(V1));
  std::printf("sizeof(C : A, B 多重继承)=%zu  (两个 vptr)\n", sizeof(C));
  std::printf("sizeof(E 菱形虚继承)=%zu\n", sizeof(E));

  C c;
  A* pa = &c; B* pb = &c;
  std::printf("== 多重继承的 this 调整 ==\n");
  std::printf("(A*)==&c ? %s；B* 比 A* 多偏移 %td 字节（B 子对象在 C 对象内部，指针值不同）\n", (void*)pa == (void*)&c ? "是" : "否", (char*)pb - (char*)pa);
  std::printf("static_cast<C*>(pb)==&c ? %s\n", static_cast<C*>(pb) == &c ? "是（编译器减去偏移）" : "否");

  Der1 d1a, d1b; Der2 d2; Base1 b1;
  std::printf("== 同一动态类型共享 vtable 指针 ==\n");
  std::printf("Der1 对象甲 vptr==对象乙 vptr ? %s\n", vptr_of(&d1a) == vptr_of(&d1b) ? "是" : "否");
  std::printf("Der1 与 Der2 vptr 相同 ? %s\n", vptr_of(&d1a) == vptr_of(&d2) ? "是" : "否");
  std::printf("Base1 与 Der2 vptr 相同 ? %s (即使 Der2 没加成员，它也有自己的 vtable)\n", vptr_of(&b1) == vptr_of(&d2) ? "是" : "否");
  std::printf("== 构造期间动态类型 ==\n");
  struct P { P() { who(); } virtual void who() { std::puts("  P::who"); } };
  struct Q : P { void who() override { std::puts("  Q::who"); } };
  Q q; (void)q; // 基类构造函数里调用虚函数，只会调到 P::who
}
```

运行结果（地址和偏移取决于 ABI，这里是 g++ 13 / x86-64 Linux）：

```text
== 填充与重排 ==
Bad{char,double,char,int}  sizeof=24
Good{double,int,char,char} sizeof=16
offsetof(Bad,b)=8 offsetof(Bad,c)=16 offsetof(Bad,d)=20
== 空类 ==
sizeof(Empty)=1  成员为 Empty: 8  [[no_unique_address]]: 4
alignas(64) struct: sizeof=64 alignof=64
== 虚函数与继承 ==
sizeof(V0)=4  sizeof(V1 有虚函数)=16  (8 字节 vptr + 4 字节 int + 4 字节对齐填充)
sizeof(C : A, B 多重继承)=32  (两个 vptr)
sizeof(E 菱形虚继承)=40
== 多重继承的 this 调整 ==
(A*)==&c ? 是；B* 比 A* 多偏移 16 字节（B 子对象在 C 对象内部，指针值不同）
static_cast<C*>(pb)==&c ? 是（编译器减去偏移）
== 同一动态类型共享 vtable 指针 ==
Der1 对象甲 vptr==对象乙 vptr ? 是
Der1 与 Der2 vptr 相同 ? 否
Base1 与 Der2 vptr 相同 ? 否 (即使 Der2 没加成员，它也有自己的 vtable)
== 构造期间动态类型 ==
  P::who
```

重点解读：

- `Bad` 和 `Good` 成员完全一样，只因声明顺序不同，大小是 24 对 16。在大数组里，这直接影响缓存（cache）利用率。
- `WithEmptyMember` 是 8，`WithNoUnique` 是 4：空成员浪费了一个对齐（alignment）单位，`[[no_unique_address]]` 把它省掉了。
- `sizeof(V1)` 是 16，而不是 4+8：vptr 8 字节，`int` 4 字节，再加 4 字节填充（padding）让大小对齐到 8 的倍数。
- 多重继承（multiple inheritance）时，`(B*)` 的值比 `(A*)` 多一个偏移。这解释了一个经典面试题：**为什么多重继承下不能用 `reinterpret_cast` 或 C 风格强转来在基类指针之间转换**——`static_cast`/`dynamic_cast` 会做偏移调整，`reinterpret_cast` 不会。
- `Base1` 和 `Der2` 的 vptr 不同：即使派生类没有加任何成员，只要重写了虚函数（virtual function）就有自己的 vtable。
- 在 `P` 的构造函数里调用 `who()`，打印的是 `P::who`，不是 `Q::who`。

### 1.6 其他必须知道的布局知识

- **标准布局（standard-layout）与平凡（trivial）类型**：标准布局类型可以和 C 互操作，第一个成员的地址等于对象地址，`offsetof` 对它才合法；平凡可拷贝（trivially copyable）类型可以用 `memcpy` 搬运。判断用 `std::is_standard_layout_v`、`std::is_trivially_copyable_v`。
- **位域（bit-field）**：位域的布局（顺序、跨存储单元）是实现定义的，不能取地址，多线程下相邻位域是同一个内存位置，不同线程写会数据竞争（data race）。不要用位域做可移植的二进制协议。
- **联合体（union）**：同一时刻只有一个成员是“活跃”的；读取非活跃成员是未定义行为（C++，与 C 不同）。需要类型双关（type punning）用 `std::bit_cast` 或 `memcpy`（第六章）。`std::variant` 是类型安全的联合体。
- **`this` 指针与成员函数**：成员函数就是多一个隐藏 `this` 参数的普通函数；非虚成员函数不占对象空间。`sizeof` 不包含静态成员。
- **RTTI**：`dynamic_cast` 和 `typeid` 依赖 vtable 里的 `typeinfo`。向下转换 `dynamic_cast` 要沿继承图查找，比 `static_cast` 慢得多；很多低延迟代码库用 `-fno-rtti` 关掉它。

### 1.7 对象模型面试题与答案要点

**Q1. `sizeof` 一个空类是多少？为什么？空基类优化是什么？**
至少为 1，因为 C++ 要求不同的完整对象有不同的地址。作为基类时，基类子对象和派生类对象共享起始地址也不违反规则，所以空基类可以不占空间（EBO）。`std::unique_ptr<T, EmptyDeleter>` 就是靠它做到和裸指针一样大。C++20 的 `[[no_unique_address]]` 对成员也有效。（实验 1 里 8 对 4。）

**Q2. 虚函数（virtual function）是怎么实现的？一次虚调用的成本是什么？**
见 1.4：每个对象一个 vptr，每个类一张 vtable。虚调用是“读 vptr、读槽位、间接调用”。真正的成本在于：间接分支预测（branch prediction）失败时的流水线冲刷（同一调用点的动态类型变化多时更严重）、无法内联（inlining）和随之而来的失去优化机会。**强调这是 Itanium ABI 的实现，标准没有规定 vtable。** 实验 13 里同样的函数，可内联的版本比虚调用快约 4 倍，这个差距主要是“能不能内联”，不是“虚调用本身的两次读取”。

**Q3. 为什么构造函数里调用虚函数不能多态（polymorphism）？析构函数呢？**
基类构造时，派生部分还没构造，如果这时能调到派生类的重写版本，它会访问尚未初始化的成员。所以语言规定：构造期间对象的动态类型就是正在构造的那个类（实现上是 vptr 逐层改写）。析构函数同理，派生部分已经销毁。如果调用的是纯虚函数且没有定义，是未定义行为（UB, undefined behavior）。解决：用工厂函数 + 两阶段初始化，或让派生类显式把需要的信息传给基类构造函数。

**Q4. 基类析构函数为什么要是虚的？什么时候可以不是？**
通过基类指针 `delete` 派生类对象，如果基类析构函数不是虚的，行为未定义（通常只调用基类析构，派生部分泄漏/损坏）。如果类不打算被多态地删除，可以不写虚析构，但应当让析构函数 `protected` 且非虚（防止误用），或者把类标成 `final`。带虚函数的类基本都应该有虚析构。

**Q5. 多重继承（multiple inheritance）下 `static_cast` 和 `reinterpret_cast` 有什么区别？指针值为什么会变？**
见实验 1。`static_cast` 在类层次内转换会调整偏移；`reinterpret_cast` 只是把位模式当另一种类型，不会调整。第二个基类的子对象位于派生对象的内部偏移处，所以转换为它时指针值改变；空指针转换要特殊处理，保持空。

**Q6. 虚继承（virtual inheritance）解决什么问题？代价是什么？**
解决菱形继承里公共基类被复制两份的问题。代价：对象更大（有虚基类偏移）、访问虚基类成员要多一次间接寻址、构造顺序特殊（最派生类直接构造虚基类）、`static_cast` 向下转换虚基类不允许（需要 `dynamic_cast`）。现代设计倾向于避免菱形继承，用组合或接口类。

**Q7. 什么是对象切片？怎么避免？**
把派生类对象按值赋给/传给基类类型，只拷贝基类部分，虚函数行为丢失。避免：多态类型按引用/指针传递；基类禁用拷贝（`= delete`）并提供 `clone()`；用 `std::unique_ptr<Base>` 存储。（见实验 17 的第 5 项：按值传递打印 `Animal`，按引用打印 `Cat`。）

**Q8. 什么是 `final`、`override`？它们的作用？**
`override` 让编译器检查“确实重写了某个虚函数”，拼错签名会编译失败；`final` 禁止进一步重写或继承。`final` 还给优化器提供信息：编译器知道没有更派生的类型，可以把虚调用去虚拟化（devirtualization）。

**Q9. 解释 `dynamic_cast` 的开销和替代方案。**
需要 RTTI；向下转换沿继承图查找（字符串比较 typeinfo 名称在某些实现里很慢）。替代：设计上避免向下转换（访问者模式、虚函数、`std::variant` + `std::visit`），或自己带类型标签 + `static_cast`（要保证标签正确）。

**Q10. 空指针调用成员函数一定崩溃吗？**
不一定，但这是未定义行为。非虚成员函数只是多一个 `this` 参数，如果不访问成员，在某些实现上“碰巧能跑”；虚函数调用要读 vptr，会崩溃。**不要依赖。** 优化器还可能因为“`this` 不可能是空”而删除后面的空指针检查（见第六章）。

**Q11. 解释 `alignas`、`alignof`，什么时候需要？**
需要 SIMD 向量（对齐（alignment）加载指令）、避免伪共享（false sharing）（独占缓存行（cache line））、与硬件寄存器/DMA 缓冲区对齐、对象跨缓存行影响性能时。C++17 起，`new` 会自动用对齐版本的 `operator new` 分配过度对齐类型；自定义分配器（allocator）要自己处理对齐。

**Q12. POD、平凡类型、标准布局（standard-layout）类型的区别？为什么重要？**
C++20 起 POD 概念被弃用，改为分别判断“平凡”（trivial，构造/拷贝/析构都是平凡的）和“标准布局”。重要性：平凡可拷贝（trivially copyable）才能安全 `memcpy`/放进共享内存/做二进制序列化；标准布局才能与 C 互操作、`offsetof`。

---

## 二、值类别、移动语义与完美转发

### 2.1 为什么需要移动语义

没有移动语义（move semantics）时，把一个大的 `std::vector` 从函数返回、放进容器，要么拷贝所有元素（慢），要么用指针（丢了值语义和 RAII）。移动语义的核心想法：**如果源对象马上就要销毁（是个临时对象），就不必拷贝，直接“偷”它的资源**（比如把内部指针换过来），留给源对象一个“有效但未指定”的状态。

### 2.2 值类别（value category）

每个表达式有两个独立的属性：**有没有身份**（能不能取地址、是不是指向某个具体对象）和**能不能被移动**。

| | 有身份 | 无身份 |
|---|---|---|
| 可移动 | xvalue（将亡值，如 `std::move(x)`、返回右值引用的函数调用） | prvalue（纯右值，如 `42`、`T{}`、返回值为 T 的函数调用） |
| 不可移动 | lvalue（左值，如变量名、`*p`） | — |

glvalue = lvalue + xvalue；rvalue = xvalue + prvalue。

**最容易混淆的一点**：**一个有名字的右值引用变量本身是左值**。`void f(T&& x) { g(x); }` 里的 `x` 是左值，所以 `g(x)` 调用的是 `g(const T&)` 或 `g(T&)`，不是 `g(T&&)`。要继续当右值传下去，必须 `g(std::move(x))`（确定是右值引用时）或 `g(std::forward<T>(x))`（转发引用（forwarding reference）时）。

### 2.3 `std::move` 与 `std::forward` 到底做什么

- `std::move(x)` **什么也不移动**，它只是 `static_cast<remove_reference_t<T>&&>(x)`：把表达式转换成右值（xvalue）。真正的移动发生在**接收这个右值的移动构造函数/移动赋值运算符**里。
- 对 `const` 对象 `std::move` 得到的是 `const T&&`，它匹配不了 `T(T&&)`，只能匹配 `T(const T&)`——**悄悄变成拷贝**（实验 2 的最后一行 `std::move` 一个 const 对象）。
- **转发引用（forwarding reference，也叫万能引用）**：`template <class T> void f(T&& x)` 里的 `T&&`，或 `auto&&`。传入左值（lvalue）时 `T` 推导为 `X&`，经过**引用折叠（reference collapsing）**（`X& &&` 折叠成 `X&`）参数类型是左值引用；传入右值时 `T` 推导为 `X`，参数是 `X&&`。`std::forward<T>(x)` 在 `T` 是左值引用类型时返回左值引用，否则返回右值引用——**保持传入时的值类别（value category）**。
- 引用折叠规则：只要有一个是左值引用，结果就是左值引用；两个都是右值引用才是右值引用。
- `T&&` **不总是**转发引用：只有在“正在被推导的模板参数”上才是（`vector<T>&&` 里的 `T&&` 不是；类模板成员函数 `void push_back(T&&)` 里的 `T` 已经确定，也不是）。

### 2.4 拷贝省略（copy elision）与返回值优化

- **C++17 起，从纯右值（prvalue）初始化同类型对象是“强制省略”**：`T make() { return T(1); }`、`T t = make();` 没有任何拷贝或移动，甚至不要求有可访问的拷贝/移动构造函数。
- **NRVO（具名返回值优化）**：`T make() { T t; ...; return t; }` 允许省略，但**不是强制**，编译器可能做也可能不做。即使不省略，`return t;` 也会先尝试把 `t` 当右值（rvalue，走移动构造），所以不要写 `return std::move(t);`。
- **`return std::move(t);` 是画蛇添足**：它把表达式变成 `T&&`，**不再是“返回局部变量名”**，因此阻止了 NRVO，反而强制多一次移动。GCC 的 `-Wpessimizing-move` 会警告（实验 2 里编译时能看到）。
- 有多个候选返回对象（`if (b) return x; return y;`）时，NRVO 通常无法应用，仍会走移动（实验 2 第 4 行）。

### 2.5 特殊成员函数：零法则、三法则、五法则

- **五个**：析构函数、拷贝构造、拷贝赋值、移动构造、移动赋值。
- **三法则（rule of three）**：如果你需要自己写其中一个（析构/拷贝构造/拷贝赋值），多半三个都要写（管理资源的类）。
- **五法则（rule of five）**：C++11 以后加上两个移动操作。
- **零法则（rule of zero）**：优先让成员自己管理资源（`std::vector`、`std::unique_ptr`、`std::string`），你的类就**一个都不用写**，编译器生成的恰好正确。
- **编译器自动生成规则**（面试常问）：声明了拷贝操作或析构函数 → **不会**自动生成移动操作（会退回拷贝，没有任何报错）；声明了移动操作 → 拷贝操作被隐式删除。所以“只写了析构函数的类，移动全变拷贝”是个常见的性能陷阱。
- 移动操作应当 `noexcept`（下一节原因）。

### 2.6 实验 2：数一数拷贝和移动

```cpp
// 实验 2：拷贝与移动到底发生了几次？值类别、返回值优化、noexcept 对 vector 扩容的影响、完美转发。
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

struct T {
  static inline int copies = 0, moves = 0, ctors = 0;
  int id;
  explicit T(int i = 0) : id(i) { ++ctors; }
  T(const T& o) : id(o.id) { ++copies; }
  T(T&& o) noexcept : id(o.id) { ++moves; }
  T& operator=(const T&) = default;
  T& operator=(T&&) noexcept = default;
  static void reset() { copies = moves = ctors = 0; }
  static void show(const char* what) { std::printf("%-46s 构造 %d  拷贝 %d  移动 %d\n", what, ctors, copies, moves); reset(); }
};

struct U {  // 移动构造没有 noexcept
  static inline int copies = 0, moves = 0;
  int id;
  explicit U(int i = 0) : id(i) {}
  U(const U& o) : id(o.id) { ++copies; }
  U(U&& o) : id(o.id) { ++moves; }
};

T make_prvalue() { return T(1); }                 // C++17 起保证不产生临时对象
T make_nrvo() { T t(2); return t; }                // NRVO：允许省略，GCC/Clang 通常会省略
T make_move_return() { T t(3); return std::move(t); }  // 画蛇添足：阻止了 NRVO
T make_conditional(bool b) { T x(4), y(5); if (b) return x; return y; }  // 两个候选，通常无法 NRVO，但仍会按移动处理

void sink(T) {}
template <class X> void fwd(X&& x) { sink(std::forward<X>(x)); }
template <class X> void no_fwd(X&& x) { sink(x); }  // 具名右值引用是左值：会拷贝

int main() {
  { T::reset(); T t = make_prvalue(); (void)t;           T::show("return T(1)   (prvalue，保证省略)"); }
  { T t = make_nrvo(); (void)t;                          T::show("T t; return t;   (NRVO)"); }
  { T t = make_move_return(); (void)t;                   T::show("return std::move(t)   (反而多一次移动)"); }
  { T t = make_conditional(true); (void)t;               T::show("两个局部变量按条件返回"); }
  { T a(1); T::reset(); T b = a; (void)b;                T::show("T b = a;"); }
  { T a(1); T::reset(); T b = std::move(a); (void)b;     T::show("T b = std::move(a);"); }
  { T a(1); T::reset(); sink(a);                         T::show("sink(T) 传左值"); }
  { T a(1); T::reset(); sink(std::move(a));              T::show("sink(T) 传 std::move"); }
  { T a(1); T::reset(); fwd(a);                          T::show("转发引用 fwd(a)，std::forward"); }
  { T::reset(); fwd(T(9));                               T::show("转发引用 fwd(T(9))，std::forward"); }
  { T::reset(); no_fwd(T(9));                            T::show("转发引用但忘了 std::forward"); }
  { const T c(1); T::reset(); T d = std::move(c); (void)d; T::show("std::move 一个 const 对象"); }

  std::puts("\n-- vector 扩容：移动构造有没有 noexcept 的区别 --");
  {
    std::vector<T> v; v.reserve(4); for (int i = 0; i < 4; ++i) v.emplace_back(i);
    T::reset(); v.push_back(T(99));  // 容量已满，触发扩容
    T::show("vector<T>   (noexcept 移动) 扩容并 push_back");
  }
  {
    std::vector<U> v; v.reserve(4); for (int i = 0; i < 4; ++i) v.emplace_back(i);
    U::copies = U::moves = 0; v.push_back(U(99));
    std::printf("%-46s 拷贝 %d  移动 %d\n", "vector<U>   (移动没有 noexcept) 扩容并 push_back", U::copies, U::moves);
  }

  std::puts("\n-- push_back 与 emplace_back --");
  { std::vector<T> v; v.reserve(8); T::reset(); v.push_back(T(1));      T::show("push_back(T(1))"); }
  { std::vector<T> v; v.reserve(8); T::reset(); v.emplace_back(1);      T::show("emplace_back(1)  (原地构造)"); }
  { std::vector<std::string> v; v.reserve(2);
    std::string s(40, 'x');  // 超过 SSO，拷贝要分配内存
    v.push_back(s); v.push_back(std::move(s));
    std::printf("std::move 之后源字符串 size=%zu（有效但未指定；libstdc++ 实际为空）\n", s.size()); }
}
```

运行结果：

```text
return T(1)   (prvalue，保证省略)         构造 1  拷贝 0  移动 0
T t; return t;   (NRVO)                        构造 1  拷贝 0  移动 0
return std::move(t)   (反而多一次移动)  构造 1  拷贝 0  移动 1
两个局部变量按条件返回              构造 2  拷贝 0  移动 1
T b = a;                                       构造 0  拷贝 1  移动 0
T b = std::move(a);                            构造 0  拷贝 0  移动 1
sink(T) 传左值                              构造 0  拷贝 1  移动 0
sink(T) 传 std::move                          构造 0  拷贝 0  移动 1
转发引用 fwd(a)，std::forward             构造 0  拷贝 1  移动 0
转发引用 fwd(T(9))，std::forward          构造 1  拷贝 0  移动 1
转发引用但忘了 std::forward             构造 1  拷贝 1  移动 0
std::move 一个 const 对象                  构造 0  拷贝 1  移动 0

-- vector 扩容：移动构造有没有 noexcept 的区别 --
vector<T>   (noexcept 移动) 扩容并 push_back 构造 1  拷贝 0  移动 5
vector<U>   (移动没有 noexcept) 扩容并 push_back 拷贝 4  移动 1

-- push_back 与 emplace_back --
push_back(T(1))                                构造 1  拷贝 0  移动 1
emplace_back(1)  (原地构造)                构造 1  拷贝 0  移动 0
std::move 之后源字符串 size=0（有效但未指定；libstdc++ 实际为空）
```

逐行读（这些就是面试答案）：

1. `return T(1)`：0 拷贝 0 移动（强制省略）。
2. NRVO：0 拷贝 0 移动（GCC 做了，标准不要求）。
3. `return std::move(t)`：多了 **1 次移动**。
4. 按条件返回两个局部变量：构造了 2 个，**1 次移动**——没有 NRVO。
5. `T b = a`：1 次拷贝；`T b = std::move(a)`：1 次移动。
6. 按值参数 `sink(T)`：传左值（lvalue）拷贝，传 `std::move` 移动。这就是“**按值传递 + 移动**”的 sink 参数惯用法：调用方决定是拷贝还是移动，函数内部再 `std::move` 给成员。
7. `fwd(T(9))` 用了 `std::forward`：1 次构造，1 次移动（临时对象 → 参数）。**忘了 `std::forward`**（`no_fwd`）：右值（rvalue）被当成左值，变成 **1 次拷贝**。
8. `std::move` 一个 `const T`：**拷贝**。
9. **vector 扩容**：元素的移动构造是 `noexcept` 时，扩容是 5 次移动（4 个旧元素 + 1 个新的），0 次拷贝；移动构造**没有** `noexcept` 时，扩容是 **4 次拷贝** + 1 次移动。原因：`std::vector` 要保证强异常安全（exception safety，`push_back` 失败时容器保持原样）。如果搬运到一半移动构造抛异常，旧元素已经被“偷”走，无法恢复；拷贝则可以在失败时丢弃新内存、旧数据完好。所以标准库用 `std::move_if_noexcept`：**能保证不抛就移动，不能保证就拷贝**（如果也不能拷贝，才只好移动）。这是“移动构造函数要标 `noexcept`”最有力的理由。
10. `emplace_back(1)` 原地构造，0 次移动；`push_back(T(1))` 构造临时再移动 1 次。

### 2.7 完美转发的陷阱

1. **转发引用（forwarding reference）构造函数“劫持”拷贝构造**：

```cpp
struct Person {
  std::string name;
  template <class T> explicit Person(T&&) { std::puts("调用了模板构造函数"); }   // 真实代码里这里会 name(std::forward<T>(n))
  Person(const Person& o) : name(o.name) { std::puts("调用了拷贝构造函数"); }
};
struct PersonFixed {   // 修法：排除“参数类型就是自己”的情况
  std::string name;
  template <class T, class = std::enable_if_t<!std::is_same_v<std::remove_cvref_t<T>, PersonFixed>>>
  explicit PersonFixed(T&& n) : name(std::forward<T>(n)) {}
  PersonFixed(const PersonFixed& o) : name(o.name) { std::puts("调用了拷贝构造函数"); }
};
```

对一个**非 const 左值（lvalue）** `p` 做 `Person q(p)`：模板版本推导出 `T = Person&`，参数类型是 `Person&`，是**精确匹配**；拷贝构造需要 `const Person&`（多一个 const），所以模板版本更优，被选中。我运行了这段代码（`snippets.cpp` 片段 B）：不加约束时，`Person q(p)` 打印“调用了模板构造函数”；加了约束的 `PersonFixed q(p)` 才调用拷贝构造函数。**如果模板构造函数里真的用这个参数去构造 `std::string`，不加约束时 `Person q(p)` 会直接编译失败**（我在第一次写这个片段时就撞上了这个编译错误）——这是现实中最常见的症状：“为什么拷贝一个对象会报一堆字符串构造的错误”。C++20 的写法是 `requires (!std::same_as<std::remove_cvref_t<T>, Person>)`。

2. **完美转发（perfect forwarding）会失败的实参**：花括号初始化列表（`f({1,2})`，无法推导）、`0` 或 `NULL` 作为空指针常量（被推导成 `int`）、重载函数名或函数模板名（不知道取哪个）、位域（bit-field，不能绑定非 const 引用）、只声明未定义的 `static const` 整型成员（需要取地址）。
3. **`auto&&` 在范围 for 里**：`for (auto&& x : container)` 对 `vector<bool>` 这种返回代理对象的容器也能工作，而 `auto&` 不行。
4. **悬空（dangling）引用**：`const T& r = f();` 把临时对象的生命周期延长到 `r` 的生命周期；但 `T&& f(T&& x) { return std::move(x); }` 这种函数返回的引用，如果参数是临时对象，在完整表达式结束后就悬空了。

### 2.8 移动后的对象

- 标准库类型被移动后处于“**有效但未指定**”的状态：可以安全地销毁、赋新值，但不要假设它的内容。实验里 `std::string` 被移动后 `size()` 是 0（libstdc++ 的实现，**不是标准保证**）。
- 自己写的移动操作应当：把资源转移走、把源对象置于可析构的状态（比如指针置空）、自赋值安全、`noexcept`。
- 移动赋值要处理**自移动赋值**（`x = std::move(x)`）：至少不崩溃。

### 2.9 移动语义面试题与答案要点

**Q13. `std::move` 做了什么？**
只做类型转换，把左值转成右值（rvalue）引用（xvalue），本身不移动任何东西。移动发生在接收它的移动构造/赋值里。对 const 对象 move 会退回拷贝。

**Q14. 区分 lvalue、prvalue、xvalue；为什么具名的右值引用是左值？**
见 2.2。具名的就有身份，可以取地址，反复使用；如果自动当作右值，第二次使用时对象已经被偷走，会出错。所以必须显式 `std::move`。

**Q15. 什么是转发引用（forwarding reference）？`std::forward` 怎么工作？**
见 2.3。`T&&` 在被推导的模板参数上；`T` 记录了值类别（value category，左值时 `T` 是 `X&`，右值时是 `X`）；`std::forward<T>` 据此返回左值引用或右值引用。要说出引用折叠（reference collapsing）。

**Q16. 为什么不要写 `return std::move(local);`？**
它阻止 NRVO，强制一次移动；`return local;` 在不能省略时也会先尝试移动。例外：返回的是成员（`return std::move(member_);`）或经过别的表达式得到的引用——这时不是“返回局部变量名”，需要显式 `move`。返回右值引用参数（`T f(T&& x) { return x; }`）在 C++20 之前也需要 `move`，C++20 放宽了隐式移动的条件，边界请以你的编译器实测为准。

**Q17. 为什么 vector 扩容时可能拷贝而不是移动？**
见实验 2：移动构造不是 `noexcept` 时，为了强异常保证，`move_if_noexcept` 选择拷贝。结论：移动操作一律标 `noexcept`，并且可以用 `static_assert(std::is_nothrow_move_constructible_v<T>)` 检查。

**Q18. 零法则（rule of zero）、三法则（rule of three）、五法则（rule of five）；什么时候编译器不生成移动操作？**
见 2.5。只写了析构/拷贝，会抑制移动的生成，移动全部退化成拷贝。如果你要自定义析构函数，又想保留默认行为，写 `T(T&&) = default;` 等显式声明。

**Q19. `push_back` 和 `emplace_back` 有什么区别？emplace 一定更快吗？**
`push_back(T(...))` 先构造临时对象再移动进去，`emplace_back(args...)` 把参数转发给元素的构造函数，原地构造（实验 2：0 次移动对 1 次）。但对于已经有的对象，两者都要拷贝/移动，没区别；emplace 对 `explicit` 构造函数也会调用（有时造成意外），而且参数是花括号时无法转发。

**Q20. 解释 sink 参数（按值传递然后 `std::move`）。什么时候不该这样做？**
构造函数/setter 要“拿走”一个值时：`void set(std::string s) { name_ = std::move(s); }`。调用方传左值拷贝一次，传右值移动一次，只写一个函数。缺点：每次调用都至少有一次移动；对于拷贝很便宜的类型无所谓；如果函数在某些路径下并不真的使用这个值，按值传递的拷贝就浪费了；对于需要“可能不拷贝”的场合（比如容器的 `insert`），用转发引用重载更优。

**Q21. 什么是引用折叠？**
`T& &`、`T& &&`、`T&& &` 都折叠为 `T&`，只有 `T&& &&` 折叠为 `T&&`。这是转发引用能同时接受左值和右值的语言机制，也用于 `auto&&` 和 `decltype`。

**Q22. 什么是强制拷贝省略（C++17 保证省略）？它改变了什么？**
从同类型纯右值初始化对象，不再产生临时对象，也不要求拷贝/移动构造函数存在，因此不可移动不可拷贝的类型（如 `std::mutex`、`std::atomic`）也可以按值从函数返回 `return T(...)`。这是“值类别规则”本身的改变：纯右值不再是对象，而是“初始化的指令”，直到被用来初始化某个对象才物化（materialize）。

**Q23. 实现一个移动构造和移动赋值：要注意什么？**
转移资源并把源置空；`noexcept`；移动赋值先释放自己的资源，处理自赋值；或使用 copy-and-swap / move-and-swap 的统一赋值（`T& operator=(T o) noexcept { swap(o); return *this; }`，一个函数同时承担拷贝赋值和移动赋值，参数是按值的，拷贝时失败不影响 `*this`；实验 11 用的就是它）。

**Q24. 为什么 `std::vector<std::unique_ptr<T>>` 可以放入容器但不能拷贝？**
`unique_ptr` 只可移动不可拷贝，所以 vector 的拷贝构造会编译失败，但 `push_back(std::move(p))`、`emplace_back`、`std::move(vec)`、扩容（用移动）都可以。算法如 `std::sort` 对只可移动的元素类型也能工作（用移动交换元素）。


---

## 三、模板、泛型编程与编译期计算

### 3.1 为什么模板是 C++ 面试的重头戏

模板让你写一份代码，在编译期（compile time）为每种类型生成专门版本——泛型和性能兼得（STL 就是这样）。代价是：**错误信息难读、编译慢、代码膨胀（code bloat）、规则复杂**。高级面试想确认你理解模板在编译器里是怎么被处理的，而不是只会写 `template <class T>`。

### 3.2 模板的编译模型

- **两阶段查找（two-phase lookup）**：模板定义时，编译器先检查不依赖模板参数的名字（非依赖名）；实例化（instantiation）时才检查依赖名。依赖名里的函数调用通过**参数依赖查找（ADL）** 在实例化点补充查找。
- **`typename` 和 `template` 消歧义**：`T::iterator` 可能是类型也可能是静态成员，需要写 `typename T::iterator`；调用依赖对象的成员模板要写 `obj.template foo<int>()`。（C++20 起很多位置可以省略 `typename`。）
- **实例化**：隐式实例化只生成被用到的成员函数（所以类模板里某个成员函数里有只对部分类型成立的代码，只要不调用就没问题）。同一模板在多个翻译单元（translation unit）里实例化，由链接器（linker）去重（它们是“弱符号”/COMDAT）。**`extern template`** 可以告诉编译器“别在这里实例化，去别处找”，减少编译时间和目标文件体积。
- **代码膨胀（code bloat）**：`vector<int>` 和 `vector<long>` 是两份机器码。缓解：把与类型无关的部分抽到非模板基类；对指针类型共用实现（链接器 ICF 合并相同函数体）。
- **模板实现必须在头文件里**（或显式实例化），因为编译器实例化时需要看到定义。

### 3.3 重载、特化与偏特化

- 函数模板**不能偏特化（partial specialization）**，只能完全特化（specialization）或重载。重载决议会优先选非模板函数，其次选“更特化”的模板（偏序）。需要“类似偏特化”的行为时，用重载、标签分发（tag dispatch）、`if constexpr` 或把逻辑放进类模板的静态函数。
- 类模板可以偏特化，这是 `std::vector<bool>`、`std::is_pointer<T*>` 等的实现方式。
- **函数模板特化不参与重载决议**（只在选定了主模板之后才考虑特化），这是个经典陷阱，所以推荐重载而不是函数模板特化。

### 3.4 SFINAE 与 Concepts

**SFINAE**（Substitution Failure Is Not An Error，替换失败不是错误）：在重载决议中，把模板参数代入签名时如果产生无效类型，这个候选只是被丢弃，而不是报错。老式写法：

```cpp
// void_t 检测惯用法：T 是否有 .size() 成员
template <class, class = void> struct has_size : std::false_type {};
template <class T> struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};
static_assert(has_size<std::vector<int>>::value && !has_size<int>::value);
```

（这段在 `snippets.cpp` 里编译通过。）它依赖偏特化（partial specialization） + SFINAE，可读性差。**C++20 Concepts** 直接表达约束：`requires` 表达式检查“这些表达式合法”，概念可以用来约束模板参数，**错误信息直接指出哪个约束没满足**，并且**约束可以参与重载的偏序**（更受约束的重载优先，“包含关系”subsumption）。

### 3.5 实验 3：现代模板写法，全部在编译期验证

```cpp
// 实验 11：模板与元编程的现代写法（C++20）。全部在编译期验证——编译通过就说明断言成立。
#include <concepts>
#include <cstdio>
#include <string>
#include <tuple>
#include <type_traits>
#include <utility>
#include <vector>

// --- constexpr：编译期计算 ---
constexpr long long fib(int n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
static_assert(fib(20) == 6765);
consteval int sq(int x) { return x * x; }        // consteval：必须在编译期求值
constinit int g_table = sq(12);                  // constinit：保证静态初始化（避免初始化顺序问题）

// --- Concepts 取代 SFINAE ---
template <class T> concept Numeric = std::integral<T> || std::floating_point<T>;
template <class T> concept HasSize = requires(const T& t) { { t.size() } -> std::convertible_to<std::size_t>; };
template <Numeric T> T twice(T x) { return x + x; }
template <HasSize C> std::size_t count_of(const C& c) { return c.size(); }
static_assert(Numeric<int> && !Numeric<std::string>);
static_assert(HasSize<std::vector<int>> && !HasSize<int>);

// 老式 SFINAE，用来对比可读性
template <class T, std::enable_if_t<std::is_integral_v<T>, int> = 0> T old_twice(T x) { return x + x; }

// --- if constexpr：编译期分支（不满足的分支不会被实例化）---
template <class T> std::string describe(const T& v) {
  if constexpr (std::is_pointer_v<T>) return "pointer";
  else if constexpr (std::is_integral_v<T>) return "integer " + std::to_string(v);
  else if constexpr (requires { v.size(); }) return "sized container of " + std::to_string(v.size());
  else return "other";
}

// --- 折叠表达式与变参模板 ---
template <class... Ts> auto sum(Ts... xs) { return (xs + ...); }
template <class... Ts> constexpr bool all_same_v = (std::is_same_v<Ts, std::tuple_element_t<0, std::tuple<Ts...>>> && ...);
static_assert(all_same_v<int, int, int> && !all_same_v<int, long>);
template <class F, class... Args> void for_each_arg(F&& f, Args&&... args) { (f(std::forward<Args>(args)), ...); }

// --- CRTP：静态多态 ---
template <class D> struct Printable { void print() const { std::printf("%s\n", static_cast<const D*>(this)->name()); } };
struct Dog : Printable<Dog> { const char* name() const { return "Dog"; } };

// --- 类型推导 ---
int g = 1; int& ref() { return g; }
static_assert(std::is_same_v<decltype(auto(ref())), int>);          // C++23 的 auto(x) 退化拷贝；GCC 13 支持
static_assert(std::is_same_v<decltype(ref()), int&>);
static_assert(std::is_same_v<decltype((g)), int&>);                 // 带括号的变量名是左值表达式，decltype 给出引用
static_assert(std::is_same_v<decltype(g), int>);
template <class T> void deduce(T&&) {}                              // 转发引用
template <class T> constexpr bool is_lvalue_deduced(T&&) { return std::is_lvalue_reference_v<T>; }

int main() {
  int a = 3; const int& cr = a;
  std::printf("twice(21)=%d  twice(1.5)=%.1f  old_twice(4)=%d  count_of(vector)=%zu\n", twice(21), twice(1.5), old_twice(4), count_of(std::vector<int>(5)));
  std::printf("describe: %s | %s | %s | %s\n", describe(&a).c_str(), describe(7).c_str(), describe(std::string("abc")).c_str(), describe(2.5).c_str());
  std::printf("sum(1,2,3,4)=%d  g_table=%d\n", sum(1, 2, 3, 4), g_table);
  Dog().print();
  std::printf("is_lvalue_deduced(a)=%d  (cr)=%d  (7)=%d  (std::move(a))=%d\n", is_lvalue_deduced(a), is_lvalue_deduced(cr), is_lvalue_deduced(7), is_lvalue_deduced(std::move(a)));
  for_each_arg([](auto&& x) { std::printf("[%s] ", describe(x).c_str()); }, 1, std::string("hi"), 3.5);
  std::puts("");
}
```

运行结果：

```text
twice(21)=42  twice(1.5)=3.0  old_twice(4)=8  count_of(vector)=5
describe: pointer | integer 7 | sized container of 3 | other
sum(1,2,3,4)=10  g_table=144
Dog
is_lvalue_deduced(a)=1  (cr)=1  (7)=0  (std::move(a))=0
[integer 1] [sized container of 2] [other] 
--- concept 约束不满足的报错 ---
concept_error.cpp: In function 'int main()':
concept_error.cpp:5:26: error: no matching function for call to 'twice(std::string)'
concept_error.cpp:4:30: note: candidate: 'template<class T>  requires  integral<T> T twice(T)'
concept_error.cpp:4:30: note:   template argument deduction/substitution failed:
--- 无约束模板误用：诊断总行数 ---
112
no_concept_error.cpp: In function 'int main()':
```

注意程序里的 `static_assert` 都是**编译期（compile time）**检查：如果任何一个不成立，这个文件根本编不过。重点：

- `constexpr` 函数可以在编译期或运行期（run time）执行；`consteval` 必须在编译期执行；`constinit` 保证变量是**静态初始化**（编译期常量初始化），避免初始化顺序问题（第十章）。
- `if constexpr` 的未选中分支**不会被实例化（instantiation）**，所以同一函数模板里可以针对指针、整数、容器写不同分支，不会因为其他类型没有 `.size()` 而编译失败（`describe(&a)` 走指针分支）。
- 折叠表达式（fold expression） `(xs + ...)` 把参数包展开为二元运算；逗号折叠 `(f(args), ...)` 对每个参数调用一次。
- `decltype((g))` 是 `int&` 而 `decltype(g)` 是 `int`：**带括号的变量名是左值表达式**，`decltype` 给出引用类型。
- `is_lvalue_deduced` 说明 `T&&` 对左值推导为左值引用，对右值（rvalue，包括 `std::move(a)`）推导为非引用。

**Concepts 的报错 vs 无约束模板的报错**（用同一个编译器实测）：

- 调用 `twice(std::string("a"))`，而 `twice` 要求 `std::integral`：g++ 的报错是 `no matching function for call to 'twice(std::string)'`，随后指出 `constraints not satisfied`，几行就结束，错误出现在调用点。
- 给 `std::accumulate` 传一个无法相加的类型：诊断共 112 行，真正的错误出现在标准库 `<numeric>` 头文件的深处。

（两项的具体输出见上面运行结果的后半部分。）**这是 Concepts 最实际的价值：把错误从模板内部挪到调用点。**

### 3.6 类型推导规则

- **模板推导 `template <class T> void f(T param)`**：忽略引用和顶层 const（按值拷贝）。`f(T& param)`：保留 const。`f(T&& param)`：左值（lvalue）得到引用（转发引用（forwarding reference））。数组名/函数名按值时退化为指针，按引用时保留数组类型（可以推导数组大小）。
- **`auto`** 的推导规则和模板一样，唯一的例外是花括号：`auto x = {1}` 是 `std::initializer_list<int>`，`auto x{1}`（C++17 起）是 `int`。实验 17 的第 7 项印证了 `auto a = {1}` 是 `std::initializer_list<int>`（`typeid` 名字 `St16initializer_listIiE`）。
- **`decltype(expr)`**：不带括号的标识符给出声明类型；其他表达式按值类别（value category）：左值 → `T&`，xvalue → `T&&`，prvalue → `T`。
- **`decltype(auto)`**：用 `decltype` 的规则推导返回类型，常用于完美转发（perfect forwarding）返回值 `decltype(auto) f() { return g(); }` 保留引用性。
- **CTAD（类模板参数推导）**：`std::vector v{1,2,3};`、`std::pair p(1, "x");`。可以写推导指引（deduction guide）。

### 3.7 常用的模板技巧

- **CRTP（奇异递归模板模式）**：`struct D : Base<D>`，基类通过 `static_cast<D*>(this)` 调用派生类的函数，实现**静态多态（static polymorphism）**，没有虚表、可内联（inlining，实验 13：可内联的调用比虚调用快约 4 倍）。缺点：不能运行期（run time）多态（polymorphism）地持有不同类型；C++23 的**显式对象形参**（deducing this）可以替代很多 CRTP 场景。
- **类型擦除（type erasure）**：外层是值语义的普通类，内部持有抽象基类指针，具体类型在模板派生类里。`std::function`、`std::any`、`std::shared_ptr` 的删除器都是这个套路（第九章有完整实现）。
- **策略类（policy-based design）**：把算法的某一方面作为模板参数，如 `std::unique_ptr<T, Deleter>`、`std::vector<T, Allocator>`。
- **标签分发**：用空类型作为重载的区分标签，如迭代器类别 `random_access_iterator_tag`；C++17 起多用 `if constexpr`，C++20 用概念。
- **SFINAE 友好的特性检测**：`std::is_invocable_v`、`std::is_constructible_v`、`requires`。
- **非类型模板参数（NTTP）**：整数、指针，C++20 起可以是字面量类类型和浮点数。
- **变参模板**与**折叠表达式（fold expression）**，`sizeof...(Ts)`，递归展开（旧）→ 折叠（新）。

### 3.8 模板面试题与答案要点

**Q25. 解释两阶段查找（two-phase lookup）。为什么调用基类（依赖基类）的成员函数要写 `this->f()`？**
`template <class T> struct D : Base<T> { void g() { f(); } };`：`f` 是非依赖名，定义时就要查找，而依赖基类 `Base<T>` 在定义时还不知道内容（可能有特化（specialization）），所以不会去基类里找，导致找不到。写 `this->f()`、`Base<T>::f()` 或 `using Base<T>::f;` 把它变成依赖名，推迟到实例化（instantiation）时查找。

**Q26. 什么是 SFINAE？它和 Concepts 的关系？**
见 3.4。SFINAE 是替换失败时丢弃候选而非报错；Concepts 是语言层面的约束，可读性好、报错好、能参与偏序。

**Q27. `typename` 和 `template` 关键字什么时候需要？**
见 3.2。依赖名默认当作值；要当类型就加 `typename`；要当成员模板就加 `template` 前缀。

**Q28. 函数模板能偏特化（partial specialization）吗？为什么推荐重载？**
不能。函数模板特化不参与重载决议，容易得到出乎意料的结果；通过重载（或类模板的静态成员）实现。

**Q29. 解释 `if constexpr` 与普通 `if` 的区别。**
`if constexpr` 的条件在编译期（compile time）求值，未选中的分支在模板里**不会被实例化**，即使代码对当前类型无效也行；普通 `if` 两个分支都必须能编译。

**Q30. 解释 `auto` 与 `decltype(auto)` 的区别。给出一个会出错的例子。**
`auto` 会丢掉引用和顶层 const；`decltype(auto)` 保留。例：`decltype(auto) f() { int x = 0; return (x); }` 返回 `int&`，是对局部变量的悬空（dangling）引用（因为括号让 `decltype` 看成左值（lvalue）表达式）；而 `return x;` 返回 `int`。

**Q31. 为什么模板的定义通常放在头文件里？**
实例化时需要完整定义。若放在 .cpp 里，其他翻译单元（translation unit）用到的实例没有被生成，链接失败；可以用显式实例化（`template class Foo<int>;`）并在头里声明 `extern template`。

**Q32. `constexpr`、`consteval`、`constinit` 的区别？**
`constexpr`：可以在编译期求值（也可运行期（run time））；`consteval`：必须编译期；`constinit`：变量必须静态初始化，但本身不是 const，可以运行期修改。`constinit` 的价值是避免“静态初始化顺序（static initialization order）灾难”（第十章实验）。

**Q33. 什么是 CRTP？优缺点？**
见 3.7。

**Q34. 实现 `std::is_same`、`std::enable_if`、`std::remove_reference`。**
都是偏特化：`template <class T, class U> struct is_same : false_type {}; template <class T> struct is_same<T, T> : true_type {};`；`enable_if<true, T>` 特化有 `type`，`false` 版本没有；`remove_reference<T&>` 特化去掉引用。能默写这三个说明你理解类模板偏特化。

**Q35. 模板导致的编译时间爆炸怎么处理？**
`extern template`、预编译头/模块（modules）、减少头文件包含、把模板中与类型无关的部分抽出、用前置声明、避免在头文件里做重型元编程、用 `constexpr` 函数代替递归模板、查看 `-ftime-trace`（Clang）找热点。

**Q36. 变参模板怎么展开？折叠表达式（fold expression）有哪几种？**
一元左折叠 `(... op pack)`、一元右折叠 `(pack op ...)`、二元折叠 `(init op ... op pack)`。逗号运算符折叠可对每个元素执行副作用。

**Q37. 概念的“包含关系”（subsumption）是什么？**
如果一个概念由另一个用 `&&` 组合而成，则前者比后者“更受约束”，重载决议会选择更受约束的模板。这使得 `template <std::integral T>` 和 `template <std::signed_integral T>` 两个重载并存时，传 `int` 优先选后者。（需要约束表达式的“原子性”被编译器识别为相同。）

**Q38. 解释 `std::declval`。**
在不求值的上下文（`decltype`、`noexcept`、`requires`）中，假装拥有一个 `T` 的右值（rvalue）引用，用来检查表达式合法性和类型，而不需要 `T` 有默认构造函数。它只能出现在不求值的上下文，否则链接失败。

**Q39. 如何在编译期检查一个类型是否有某个成员函数？**
老办法：`void_t` + `decltype` 偏特化（3.4）；现代：`requires` 表达式的概念，或 `requires { t.size(); }` 在 `if constexpr` 里直接用（实验 3 的 `describe`）。

---

## 四、内存管理、所有权与对象生命周期

### 4.1 为什么内存管理是 C++ 的核心

没有垃圾回收意味着**你决定每个对象何时生、何时死**。C++ 给出的工具是 **RAII（资源获取即初始化）**：把资源的生命周期绑定到对象的生命周期，用析构函数保证释放，不管是正常返回、提前返回还是异常。现代 C++ 的原则：**默认值语义；需要堆就用 `unique_ptr`；真的需要共享所有权才用 `shared_ptr`；裸指针只表示“非拥有的观察”。**

### 4.2 `new`/`delete` 的真实含义

- **new 表达式**做两件事：调用 `operator new` 分配**原始内存**；在这块内存上调用构造函数。**delete 表达式**：先调用析构函数，再调用 `operator delete` 释放内存。
- `operator new` 是普通函数，可以重载（全局的或类专属的）。**placement new**：`new (ptr) T(args)` 只做第二步，在给定地址上构造对象；对应地要手动调用析构函数 `p->~T()`。
- `new[]` / `delete[]` 必须配对；`delete` 一个 `new[]` 的数组是未定义行为（UB, undefined behavior，`new[]` 可能在前面存了元素个数以便调用每个析构函数）。
- **分配失败**：默认抛 `std::bad_alloc`；`new (std::nothrow)` 返回空指针。
- **对象生命周期**：对象的生命周期从构造完成开始，到析构开始结束。在生命周期之外访问对象（悬空指针（dangling pointer）、释放后使用）是未定义行为。C++17 的 `std::launder` 用于在重新使用同一块存储创建新对象后，获得指向新对象的合法指针（高级话题，极少需要）。
- **对齐（alignment）**：C++17 的 `operator new(size_t, align_val_t)` 保证过度对齐。

### 4.3 分配器与自定义内存管理

为什么需要：`malloc` 是通用的——线程安全、处理任意大小、可能有锁、延迟不稳定；而你的程序往往有明显的模式（大量同尺寸小对象、生命周期成批结束）。常见方案：

- **对象池（object pool）/空闲链表**：固定大小块，分配释放都是 O(1)，没有碎片。
- **竞技场/线性分配器（arena, bump allocator）**：只增加指针，一次性整体释放。适合“一次请求/一帧”内的所有分配。
- **`std::pmr`（多态（polymorphism）内存资源，C++17）**：容器类型 `std::pmr::vector<T>` 持有一个指向 `memory_resource` 的指针，分配策略可在运行期（run time）更换，而容器类型不变（传统 `std::allocator` 模板参数会改变类型）。内置 `monotonic_buffer_resource`（竞技场）、`unsynchronized_pool_resource`、`synchronized_pool_resource`。

```cpp
std::array<std::byte, 4096> buf;
std::pmr::monotonic_buffer_resource pool(buf.data(), buf.size(), std::pmr::null_memory_resource());
std::pmr::vector<int> pv(&pool);
for (int i = 0; i < 100; ++i) pv.push_back(i);
```

这段在 `snippets.cpp` 的片段 H 里运行过：100 个 `int` 全部放进栈上缓冲区，没有碰全局堆（缓冲区用完时由于上游是 `null_memory_resource` 会抛 `bad_alloc`，而不是悄悄退回堆）。

- **第三方分配器**：jemalloc、tcmalloc、mimalloc，主要改进是线程缓存（cache，减少锁竞争）、大小分级（减少碎片）。排查内存碎片或分配热点时，换分配器通常是最快的实验。
- **低延迟场景的原则**：热路径上不分配；启动时预分配；用固定容量容器；避免 `std::string` 和 `std::function` 在热路径上隐式分配。

### 4.4 智能指针的真实样子

**`std::unique_ptr`**：独占所有权，只可移动。大小和裸指针相同（无状态删除器（deleter）时）。删除器是类型的一部分：无捕获 lambda 不占空间（空基类优化（EBO, empty base optimization）），函数指针或 `std::function` 作为删除器会增大对象。

```cpp
// 管理 C 资源：无状态 lambda 作为删除器，sizeof 仍是 8
using FilePtr = std::unique_ptr<std::FILE, decltype([](std::FILE* f) { if (f) std::fclose(f); })>;
```

（C++20 允许 lambda 出现在未求值的 `decltype` 中；片段 C 在 `snippets.cpp` 里验证了 `sizeof(FilePtr) == 8`。）

**`std::shared_ptr`**：共享所有权，引用计数（reference counting）放在**控制块（control block）**里，控制块在堆上，包含：强引用计数、弱引用计数、删除器、分配器（allocator）、（`make_shared` 时）对象本身。`shared_ptr` 对象本身是两个指针（16 字节）：一个指向对象，一个指向控制块。

- **线程安全性**：**控制块里的计数是原子的**，所以多个线程各自拥有的 `shared_ptr` 副本，可以并发（concurrency）拷贝/销毁；但是**同一个 `shared_ptr` 对象**被多个线程同时读写（比如一个线程 `reset`，另一个拷贝它）是数据竞争（data race），需要自己同步或使用 C++20 的 `std::atomic<std::shared_ptr<T>>`。**所指向的对象本身的线程安全**也不由 `shared_ptr` 保证。
- **`make_shared` vs `shared_ptr(new T)`**：前者只分配一次（对象和控制块在同一块内存），更快、更缓存（cache）友好；缺点是只要还有 `weak_ptr`，整块内存（包括已析构对象的空间）就不能归还；也无法使用自定义的 `operator new`/私有构造函数。
- **`enable_shared_from_this`**：让对象能安全地得到指向自己的 `shared_ptr`，不会创建第二个控制块。**前提是对象已经被某个 `shared_ptr` 管理**，否则抛 `bad_weak_ptr`（C++17 起；之前是未定义行为（UB, undefined behavior））。
- **别名构造（aliasing constructor）**：`shared_ptr<U>(owner, ptr)`，共享 `owner` 的控制块，但指向 `ptr`（比如成员或数组元素），使成员的生命周期绑定在整个对象上。
- **`weak_ptr`**：不拥有，用来打破循环引用（circular reference）和做缓存/观察。`lock()` 返回一个 `shared_ptr`（可能为空），必须在使用前检查。
- **循环引用泄漏**：A 持有指向 B 的 `shared_ptr`，B 也持有指向 A 的，计数永远不到 0。办法：一方改成 `weak_ptr`，或者改成非拥有的裸指针/索引。
- **绝不能用同一个裸指针构造两个 `shared_ptr`**：会创建两个独立的控制块，各自 delete 一次（双重释放）。

### 4.5 实验 4：智能指针的大小、分配次数与陷阱

```cpp
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
```

运行结果：

```text
== 大小 ==
sizeof(Widget*)=8  unique_ptr<W>=8  unique_ptr<W,无捕获lambda>=8  unique_ptr<W,函数指针>=16  unique_ptr<W,std::function>=40
shared_ptr<W>=16  weak_ptr<W>=16 （一个指向对象，一个指向控制块）
== 分配次数 ==
shared_ptr<W>(new W)      : 2 次堆分配
make_shared<W>()          : 1 次堆分配（对象和控制块一起）
make_unique<W>()          : 1 次堆分配
== 循环引用泄漏 ==
shared_ptr 成环：两个 Node 离开作用域后析构了 0 个（泄漏）
一边改成 weak_ptr：析构了 2 个（正常）
== make_shared 与 weak_ptr：内存什么时候真正释放 ==
最后一个 shared_ptr 销毁后，对象已析构(live=0)。注意：make_shared 把对象和控制块放在同一块内存里，只要还有 weak_ptr，这块内存就不归还（这一点这里没有测量，是实现行为）
== 别名构造 ==
通过 shared_ptr<int> 指向成员，却共享 Widget 的控制块：use_count=2
== enable_shared_from_this 误用 ==
栈对象上调用 shared_from_this：抛出 bad_weak_ptr（bad_weak_ptr）
由 make_shared 创建的对象：use_count=2
```

解读：

- `unique_ptr` 默认 8 字节；无捕获 lambda 删除器（deleter）仍是 8；函数指针删除器 16；`std::function` 删除器 40。**删除器的类型会让对象变大。**
- `shared_ptr` 和 `weak_ptr` 都是 16 字节。
- `shared_ptr<Widget>(new Widget)` 做了 2 次堆分配，`make_shared` 只有 1 次。
- 两个 `shared_ptr` 成环：析构了 **0** 个（泄漏）；一边改成 `weak_ptr`：析构了 2 个。
- `enable_shared_from_this` 在栈对象上调用抛 `bad_weak_ptr`；由 `make_shared` 创建的对象正常，`use_count` 为 2（`s` 和 `p`）。

### 4.6 实验 5：手写一个 `shared_ptr`（带 `weak_ptr`），并用 sanitizer 检查

手写 `shared_ptr` 是最常见的手写题之一。下面是一个简化版：控制块（control block）独立、强弱双计数、原子操作（atomic operation）、`weak_ptr::lock()` 用 CAS 循环。

```cpp
// 实验 13：手写一个简化版 shared_ptr（引用计数 + weak 计数 + 控制块），用 ASan 和 TSan 检查。
// 面试常考“手写 shared_ptr”。要点：控制块独立于对象；计数用原子；最后一个强引用释放对象，
// 最后一个（强+弱）引用释放控制块；拷贝时的 relaxed 递增、释放时的 acq_rel 递减。
#include <atomic>
#include <cstdio>
#include <thread>
#include <utility>
#include <vector>

struct ControlBlock {
  std::atomic<long> strong{1};
  std::atomic<long> weak{1};      // 所有强引用合起来算 1 个弱引用，这样“最后一个弱引用”才是释放控制块的时机
  virtual void destroy_object() noexcept = 0;
  virtual ~ControlBlock() = default;
};
template <class T> struct PtrBlock : ControlBlock {
  T* p; explicit PtrBlock(T* p) : p(p) {}
  void destroy_object() noexcept override { delete p; }
};

template <class T> class Weak;
template <class T>
class Shared {
  T* p_ = nullptr; ControlBlock* cb_ = nullptr;
  friend class Weak<T>;
 public:
  Shared() = default;
  explicit Shared(T* p) : p_(p), cb_(new PtrBlock<T>(p)) {}      // 简化：不处理构造控制块时 new 抛异常的情况（标准库会 delete p）
  Shared(const Shared& o) : p_(o.p_), cb_(o.cb_) { if (cb_) cb_->strong.fetch_add(1, std::memory_order_relaxed); }
  Shared(Shared&& o) noexcept : p_(std::exchange(o.p_, nullptr)), cb_(std::exchange(o.cb_, nullptr)) {}
  Shared& operator=(Shared o) noexcept { std::swap(p_, o.p_); std::swap(cb_, o.cb_); return *this; }
  ~Shared() {
    if (!cb_) return;
    if (cb_->strong.fetch_sub(1, std::memory_order_acq_rel) == 1) {     // 我是最后一个强引用
      cb_->destroy_object();
      if (cb_->weak.fetch_sub(1, std::memory_order_acq_rel) == 1) delete cb_;
    }
  }
  T* get() const { return p_; }
  T& operator*() const { return *p_; }
  T* operator->() const { return p_; }
  long use_count() const { return cb_ ? cb_->strong.load(std::memory_order_relaxed) : 0; }
  explicit operator bool() const { return p_ != nullptr; }
};

template <class T>
class Weak {
  T* p_ = nullptr; ControlBlock* cb_ = nullptr;
 public:
  Weak() = default;
  Weak(const Shared<T>& s) : p_(s.p_), cb_(s.cb_) { if (cb_) cb_->weak.fetch_add(1, std::memory_order_relaxed); }
  Weak(const Weak& o) : p_(o.p_), cb_(o.cb_) { if (cb_) cb_->weak.fetch_add(1, std::memory_order_relaxed); }
  ~Weak() { if (cb_ && cb_->weak.fetch_sub(1, std::memory_order_acq_rel) == 1) delete cb_; }
  Weak& operator=(const Weak&) = delete;
  Shared<T> lock() const {   // 关键：只有 strong>0 时才能“复活”一个强引用——用 CAS 循环，不能先读后加
    Shared<T> r;
    if (!cb_) return r;
    long n = cb_->strong.load(std::memory_order_relaxed);
    while (n != 0) {
      if (cb_->strong.compare_exchange_weak(n, n + 1, std::memory_order_acq_rel, std::memory_order_relaxed)) { r.p_ = p_; r.cb_ = cb_; return r; }
    }
    return r;
  }
  bool expired() const { return !cb_ || cb_->strong.load(std::memory_order_relaxed) == 0; }
};

struct Probe { static inline std::atomic<int> alive{0}; Probe() { ++alive; } ~Probe() { --alive; } int v = 7; };

int main() {
  {
    Shared<Probe> a(new Probe); Weak<Probe> w(a);
    std::printf("单线程：use_count=%ld alive=%d expired=%d\n", a.use_count(), Probe::alive.load(), w.expired());
    { Shared<Probe> b = a; std::printf("拷贝后 use_count=%ld\n", a.use_count()); }
    a = Shared<Probe>();
    std::printf("释放最后一个强引用后：alive=%d expired=%d lock()=%s\n", Probe::alive.load(), w.expired(), w.lock() ? "非空" : "空");
  }
  Shared<Probe> shared(new Probe);
  std::vector<std::thread> ts;
  std::atomic<long> locked{0};
  for (int t = 0; t < 4; ++t) ts.emplace_back([&, w = Weak<Probe>(shared)] {
    for (int i = 0; i < 100000; ++i) { Shared<Probe> c = shared; Shared<Probe> d = c; if (auto s = w.lock()) locked += s->v; }
  });
  for (auto& t : ts) t.join();
  std::printf("4 个线程各拷贝/lock 十万次后：use_count=%ld alive=%d\n", shared.use_count(), Probe::alive.load());
}
```

运行结果（ASan+UBSan 和 TSan 各跑一遍，都没有报告）：

```text
-- ASan+UBSan --
单线程：use_count=1 alive=1 expired=0
拷贝后 use_count=2
释放最后一个强引用后：alive=0 expired=1 lock()=空
4 个线程各拷贝/lock 十万次后：use_count=1 alive=1
-- TSan --
单线程：use_count=1 alive=1 expired=0
拷贝后 use_count=2
释放最后一个强引用后：alive=0 expired=1 lock()=空
4 个线程各拷贝/lock 十万次后：use_count=1 alive=1
```

面试要点：

1. **为什么弱计数从 1 开始**：所有强引用合起来算一个弱引用；这样“最后一个弱引用释放”恰好对应“没有强引用也没有弱引用”，才能安全删除控制块。
2. **`lock()` 为什么用 CAS 循环**：不能“先读 `strong > 0`，再 `fetch_add`”，两步之间可能被另一个线程把它减到 0 并销毁对象。必须原子地“当且仅当不为 0 时加 1”。
3. **内存序（memory order）**：递增可以用 `relaxed`（拿到引用的线程本来就已经通过别的方式看到了对象）；递减用 `acq_rel`，保证最后一个释放者能看到其他线程对对象的所有修改再析构它（标准库的做法是 `release` 递减加最后释放前的 `acquire` 栅栏，效果等价）。
4. **没处理的细节（这是简化版）**：控制块分配失败时释放对象、自定义删除器（deleter）、数组、`make_shared`、继承转换（`Shared<Derived>` → `Shared<Base>`）、`enable_shared_from_this`、比较与哈希。

### 4.7 其他生命周期与所有权话题

- **所有权设计**：`unique_ptr<T>` 参数表示“我接管所有权”；`const T&` / `T*` 表示“只是用一下”；`shared_ptr<T>` 参数只在函数需要共享所有权时使用（按值传递会触发原子计数增减，有开销；只想用对象就传 `const T&`）。返回 `unique_ptr<T>` 的工厂函数是首选。
- **悬空（dangling）引用的典型来源**：返回局部变量引用；`vector` 扩容后保存的指针/引用/迭代器；`std::string_view`/`std::span` 指向已销毁的字符串；lambda 按引用捕获局部变量后异步使用；容器元素的引用在 `erase` 后。
- **内存泄漏（memory leak）排查**：`valgrind --leak-check=full`（慢，不需重新编译）；`-fsanitize=address`（LeakSanitizer 随 ASan 启用）；堆剖析工具 heaptrack、jemalloc 的 profiling。
- **栈溢出（stack overflow）**：大数组放栈上、深递归。检查 `ulimit -s`；大对象用堆或 `static`；递归改成迭代或显式栈。
- **`alloca`/变长数组**：不是标准 C++，避免。

### 4.8 内存管理面试题与答案要点

**Q40. `new` 表达式和 `operator new` 的区别？placement new 是什么？**
见 4.2。new 表达式 = 分配 + 构造；`operator new` 只分配；placement new 在给定地址构造，必须手动析构，不释放内存。用途：内存池（memory pool）、容器内部（`vector` 在预留的存储上构造元素）。

**Q41. `delete` 和 `delete[]` 能混用吗？为什么？**
不能，未定义行为（UB, undefined behavior）。`new[]` 需要记录元素个数以调用每个元素的析构函数，实现常在返回的指针前面存放一个计数；`delete` 不会去那里看，既不会调对每个元素的析构，释放的地址还可能是错的。避免办法：用 `std::vector`/`std::unique_ptr<T[]>`。

**Q42. `unique_ptr`、`shared_ptr`、`weak_ptr` 的区别与使用场景？**
独占、共享、观察。默认用 `unique_ptr`，真正有共享所有权的语义（多个独立生命周期的持有者）才用 `shared_ptr`，用 `weak_ptr` 打破循环、做缓存（cache）。每个 `shared_ptr` 拷贝有原子操作（atomic operation）的成本，不要滥用。

**Q43. `shared_ptr` 是线程安全的吗？**
分三层回答：①控制块（control block）的计数操作是原子的；②不同线程各自操作自己的 `shared_ptr` 副本是安全的；③同一个 `shared_ptr` 对象被并发（concurrency）读写不安全（用 `atomic<shared_ptr>` 或加锁）；④指向的对象本身不受保护。

**Q44. `make_shared` 的优缺点？**
优点：一次分配、异常安全（exception safety，避免 `f(shared_ptr<T>(new T), g())` 在旧标准下的泄漏）、缓存友好。缺点：对象和控制块同生命周期，`weak_ptr` 存在时内存不归还；不能用自定义删除器（deleter）（有 `allocate_shared` 可自定义分配器（allocator））；不能调用私有/受保护构造函数。

**Q45. 说一下 `shared_ptr` 的循环引用（circular reference）问题以及如何排查。**
见 4.4、实验 4。排查：用 LeakSanitizer / valgrind 看泄漏的对象及其持有链；设计上明确谁拥有谁，反向的引用用 `weak_ptr`。

**Q46. `enable_shared_from_this` 的原理和陷阱？**
基类里存一个 `weak_ptr` 指向自己，在第一个 `shared_ptr` 接管对象时被初始化；`shared_from_this()` 就是 `lock()`。陷阱：在构造函数里调用（还没有 `shared_ptr` 管理）会失败；对象不是由 `shared_ptr` 管理的（栈对象/`unique_ptr`）会抛异常。

**Q47. 如何实现一个内存池/对象池（object pool）？要考虑什么？**
固定大小块 + 空闲链表（把空闲块自己的存储当作 next 指针）；对齐（alignment）；批量向系统要大块（chunk）；线程安全（线程本地池，或无锁（lock-free）链表要小心 ABA）；释放策略（整体回收 vs 逐个归还）；调试（填充（padding）模式、越界哨兵、ASan 毒化接口 `ASAN_POISON_MEMORY_REGION`）。

**Q48. 什么是 RAII？举出几个标准库中的例子。**
`lock_guard`/`scoped_lock`、`unique_ptr`、`fstream`、`vector`，以及自己写的 `scope_guard`。关键：析构函数不抛异常；资源获取失败时构造函数抛异常，已构造的成员自动销毁。

**Q49. 哪些情况下栈上对象的析构函数不会被调用？**
调用 `std::exit` / `std::abort` / `_exit`、`std::quick_exit`；未捕获的异常且实现不展开栈（`std::terminate` 前不一定展开）；进程被信号杀死；死循环；`longjmp` 越过带析构的对象（未定义行为）。

**Q50. 解释内存碎片，以及如何诊断和缓解。**
外部碎片（空闲块总量足够但没有够大的连续块）和内部碎片（分配的比请求的大）。诊断：看 RSS 与实际使用量的差距、`malloc_stats`、jemalloc 统计。缓解：换分配器、对象池、同生命周期的对象一起分配、减少大小不一的长期存活对象。

**Q51. `std::string_view` 的陷阱？**
不拥有数据，不保证以 `\0` 结尾（不能传给需要 C 字符串的 API）；指向临时字符串或已销毁字符串就悬空（dangling）。（实验 10 的 ASan 演示：`string_view` 指向离开作用域的 `std::string`，ASan 报 heap-use-after-free。）返回 `string_view` 的函数要确保底层存储活得够久。


---

## 五、并发与 C++ 内存模型

### 5.1 为什么并发题最能拉开差距

写出“大多数时候能跑”的多线程代码很容易；写出**在所有允许的执行下都正确**的并发（concurrency）代码很难。面试官用内存模型（memory model）的问题区分两类人：把 `atomic` 当成“带魔法的 int”的人，和知道**编译器和 CPU 都会重排序（reordering），而语言只保证特定的同步关系**的人。

### 5.2 基本概念

- **数据竞争（data race）**：两个线程同时访问同一个内存位置，至少一个是写，并且没有 happens-before 关系，且不都是原子操作（atomic operation）。**数据竞争是未定义行为（UB, undefined behavior）**，不是“读到旧值”这么温和。
- **互斥量与锁**：`std::mutex`；`lock_guard`（最简单的 RAII）；`unique_lock`（可延迟加锁/配合条件变量）；`scoped_lock`（C++17，同时锁多个互斥量，内部使用避免死锁（deadlock）的算法）。**锁的获取与释放构成同步**：解锁 synchronizes-with 之后的加锁。
- **死锁**的四个条件：互斥、占有并等待、不可抢占、循环等待。预防：固定加锁顺序、`std::scoped_lock`/`std::lock` 同时加多个锁、`try_lock` + 退避、减少持锁时间、不要持锁调用未知代码（回调）。
- **条件变量（condition variable）**：必须配合互斥量和**谓词**使用。`wait(lock, pred)` 等价于 `while (!pred()) wait(lock);`。要有循环/谓词是因为**虚假唤醒（spurious wakeup）** 以及“被唤醒时条件已被别的线程消耗”。丢失唤醒（先 `notify` 后 `wait`）靠谓词（共享状态）避免。通知时持不持锁都可以，持锁通知更容易推理，不持锁可能少一次无谓的唤醒再阻塞。
- **`std::thread`**：析构时如果仍然 joinable 会调用 `std::terminate`；C++20 的 `std::jthread` 在析构时自动 join，并支持 `stop_token` 协作式取消。
- **`std::async` 的坑**：返回的 `future` 的析构函数会阻塞等待任务完成（对 `launch::async` 的情况），所以不保存返回值会让“异步”调用变成同步；默认启动策略可能是延迟执行。
- **线程局部存储**：`thread_local`，每个线程一份，常用于缓存（cache）、避免共享。
- **局部静态变量的初始化是线程安全的**（C++11 起，“魔法静态”）：多个线程同时首次进入时只有一个会执行初始化，其他会等待。`std::call_once` 做同样的事。**单例的现代写法**就是函数内的 `static`；不需要手写双重检查锁。（片段 F。）
- **`volatile` 不是原子**，不提供线程间同步，只阻止编译器优化掉对它的访问（用于内存映射硬件寄存器）。多线程共享变量用 `std::atomic`。

### 5.3 原子操作与内存序（memory order）

**为什么需要内存序（memory order）**：现代编译器会重排指令，CPU 有**存储缓冲（store buffer）** 和乱序执行，所以线程 A 写的两个变量，线程 B 可能以不同的顺序看到。`std::atomic` 的操作带一个 `memory_order` 参数，说明你要多强的保证（和多少性能代价）。

| 内存序 | 保证 |
|---|---|
| `relaxed` | 只保证这个原子变量本身的操作是原子的，且对它自己有一个全局的修改顺序；**不建立任何线程间的先后关系** |
| `acquire`（用于读） | 在这次读**之后**的读写不能被重排到它之前；若读到的值是某个 `release` 写入的，则那次 release 之前的所有写入对我可见 |
| `release`（用于写） | 在这次写**之前**的读写不能被重排到它之后 |
| `acq_rel`（读-改-写） | 同时具有 acquire 和 release |
| `seq_cst`（默认） | acquire/release 的所有保证，再加上所有 `seq_cst` 操作有**一个全局的总顺序** |

核心概念是 **synchronizes-with**：线程 A 对原子变量 x 做 `store(release)`，线程 B 对同一个 x 做 `load(acquire)` 并读到了这次写入的值，则 A 中 store 之前的所有写入**happens-before** B 中 load 之后的所有读取。这就是“发布-获取”模式：**先写数据，再 release 写一个标志；另一边 acquire 读到标志，就能安全读数据。**

要点：
- **`relaxed` 适合计数器、统计**（只要最后值对就行，不用它来发布其他数据）。
- **`seq_cst` 是默认，最容易推理，也最贵**（在 x86 上，`seq_cst` 的 store 需要 `xchg` 或 `mfence`；加载是普通 `mov`。在 ARM 上则是 `stlr`/`ldar` 一类的专用指令）。
- **x86 的内存模型（memory model）较强（TSO）**：唯一允许的重排是“**后面的读可以越过前面的写**”（因为存储缓冲）。所以在 x86 上，`release`/`acquire` 通常不产生额外指令，这也意味着**x86 上跑得对不代表 ARM 上也对**。实验 6 就利用了这一点。
- **CAS（compare-and-swap）**：`compare_exchange_weak/strong(expected, desired, success_order, failure_order)`。`weak` 可能虚假失败，适合循环；`strong` 不会虚假失败。
- **ABA 问题**：线程读到值 A，被抢占，其他线程把它改成 B 又改回 A，CAS 仍然成功，但“状态”已经变了（典型：无锁（lock-free）栈弹出节点后又被复用）。解决：带版本号的指针（tagged pointer，用双宽 CAS 或指针里的空闲高位）、hazard pointer、epoch/RCU 回收。
- **内存回收是无锁结构最难的部分**：节点被其他线程可能仍在访问时不能 `delete`。方案：hazard pointers、epoch-based reclamation、引用计数（reference counting）。（据我所知 C++26 已把 hazard pointer 和 RCU 纳入标准库，**我没有核对最终文本，也没有验证**。）
- **栅栏（fence）**：`std::atomic_thread_fence(order)` 不依附于具体变量；用得少，容易用错。

### 5.4 实验 6：用“存储缓冲”测试看到真实的重排序

两个线程：线程 1 执行 `x=1; r1=y;`，线程 2 执行 `y=1; r2=x;`。如果所有操作按某种交错顺序依次执行（顺序一致），那么 `r1` 和 `r2` **不可能同时为 0**（因为至少有一个线程的 store 先于另一个线程的 load）。但 CPU 的存储缓冲（store buffer）允许“store 还在缓冲里，后面的 load 已经执行”，于是 `(0, 0)` 可能出现。

```cpp
// 实验 3：内存序的可观察后果——“存储缓冲”（store buffering）测试。
//   线程 1: x=1; r1=y;      线程 2: y=1; r2=x;
// 在顺序一致的世界里，r1 和 r2 不可能同时为 0。但每个核心有存储缓冲，store 可能晚于后面的 load 对别人可见。
// relaxed 下 (0,0) 是允许的结果，x86 上也真的会出现；seq_cst 禁止它（编译器会在 store 后加 mfence 或用 xchg）。
// 本机的结果取决于 CPU 与调度；(0,0) 出现的次数每次都不同，但 seq_cst 应该始终为 0。
#include <atomic>
#include <cstdio>
#include <thread>

template <std::memory_order STORE, std::memory_order LOAD>
long run(int iters) {
  std::atomic<int> x{0}, y{0}, go{0}, done{0};
  int r1 = 0, r2 = 0;
  long both_zero = 0;
  std::thread t1([&] {
    for (int i = 0; i < iters; ++i) {
      while (go.load(std::memory_order_acquire) != 2 * i + 1) {}
      x.store(1, STORE); r1 = y.load(LOAD);
      done.fetch_add(1, std::memory_order_acq_rel);
    }
  });
  std::thread t2([&] {
    for (int i = 0; i < iters; ++i) {
      while (go.load(std::memory_order_acquire) != 2 * i + 1) {}
      y.store(1, STORE); r2 = x.load(LOAD);
      done.fetch_add(1, std::memory_order_acq_rel);
    }
  });
  for (int i = 0; i < iters; ++i) {
    x.store(0, std::memory_order_relaxed); y.store(0, std::memory_order_relaxed);
    done.store(0, std::memory_order_relaxed);
    go.store(2 * i + 1, std::memory_order_release);
    while (done.load(std::memory_order_acquire) != 2) {}
    if (r1 == 0 && r2 == 0) ++both_zero;
  }
  t1.join(); t2.join();
  return both_zero;
}

int main() {
  const int N = 300000;
  long a = run<std::memory_order_relaxed, std::memory_order_relaxed>(N);
  long b = run<std::memory_order_release, std::memory_order_acquire>(N);
  long c = run<std::memory_order_seq_cst, std::memory_order_seq_cst>(N);
  std::printf("%d 轮中 r1==0 且 r2==0 的次数：\n", N);
  std::printf("  relaxed store / relaxed load : %ld\n", a);
  std::printf("  release store / acquire load : %ld   (release/acquire 也不禁止它)\n", b);
  std::printf("  seq_cst store / seq_cst load : %ld\n", c);
}
```

运行结果（每次运行的次数不同）：

```text
300000 轮中 r1==0 且 r2==0 的次数：
  relaxed store / relaxed load : 3714
  release store / acquire load : 4122   (release/acquire 也不禁止它)
  seq_cst store / seq_cst load : 0
```

读法：

- `relaxed`：出现了几千次 `(0,0)`——**重排序（reordering）真实发生了**，哪怕在强内存模型（memory model）的 x86 上。
- `release store / acquire load`：**同样会出现**。很多人以为 release/acquire 能防止这种情况，**不能**：release/acquire 只保证“发布-获取”这一对的可见性，不保证 store 对其他线程后续 load 的全局顺序。
- `seq_cst`：始终是 0。编译器在 store 后插入了完整栅栏（x86 上），禁止了“store 后的 load 越过 store”。

这就是“什么时候需要 `seq_cst`”的答案：当你的正确性依赖**多个独立变量上的 store→load 顺序**时（典型：Dekker/Peterson 互斥算法、某些无锁（lock-free）协议的“我先宣告，再检查你有没有宣告”）。

### 5.5 实验 7：SPSC 无锁环形队列，以及 TSan 如何帮你抓到内存序错误

SPSC（单生产者单消费者）队列是 HFT 面试里最经典的手写题。关键设计：
- 下标 `head`（消费者推进）和 `tail`（生产者推进）是原子的；各自只有一个线程写它。
- 生产者：**先写数据，再用 `release` 存储发布 `tail`**；消费者：用 `acquire` 读 `tail`，看到新值后读数据。反方向，消费者读完数据后 `release` 存储 `head`，生产者 `acquire` 读 `head` 判断是否满。
- 读自己写的下标可以用 `relaxed`（只有自己改它）。
- `head`、`tail`、数据缓冲区各自放在**不同的缓存行（cache line）**（`alignas(64)`），避免伪共享（false sharing）。
- 容量取 2 的幂，用 `& (N-1)` 代替取模。

```cpp
// 实验 4：单生产者单消费者（SPSC）无锁环形队列。
// 正确版本：生产者对 tail 做 release 存储，消费者对 tail 做 acquire 读取，从而保证“先写数据，后发布下标”。
// 错误版本（-DWRONG）：下标全用 relaxed——在 x86 上多半也能跑对，但 ThreadSanitizer 会指出数据竞争，
// 在 ARM 等弱内存序平台上则会真的读到未写好的数据。
#include <atomic>
#include <cstdio>
#include <thread>
#include <vector>

#ifdef WRONG
constexpr auto REL = std::memory_order_relaxed, ACQ = std::memory_order_relaxed;
#else
constexpr auto REL = std::memory_order_release, ACQ = std::memory_order_acquire;
#endif

template <class T, size_t N>   // N 必须是 2 的幂
class SpscQueue {
  static_assert((N & (N - 1)) == 0, "N must be power of two");
  alignas(64) std::atomic<size_t> head_{0};  // 消费者推进
  alignas(64) std::atomic<size_t> tail_{0};  // 生产者推进
  alignas(64) T buf_[N];
 public:
  bool push(const T& v) {
    size_t t = tail_.load(std::memory_order_relaxed);        // 只有自己写 tail，自己读可以 relaxed
    if (t - head_.load(ACQ) == N) return false;               // 满
    buf_[t & (N - 1)] = v;                                    // 先写数据
    tail_.store(t + 1, REL);                                  // 再发布
    return true;
  }
  bool pop(T& out) {
    size_t h = head_.load(std::memory_order_relaxed);
    if (h == tail_.load(ACQ)) return false;                   // 空
    out = buf_[h & (N - 1)];                                  // 先读数据
    head_.store(h + 1, REL);                                  // 再归还槽位
    return true;
  }
};

int main() {
  constexpr int COUNT = 200000;
  SpscQueue<int, 1024> q;
  long long sum = 0;
  std::thread prod([&] { for (int i = 1; i <= COUNT; ++i) while (!q.push(i)) {} });
  std::thread cons([&] { int v, got = 0; while (got < COUNT) if (q.pop(v)) { sum += v; ++got; } });
  prod.join(); cons.join();
  std::printf("sum=%lld 期望=%lld\n", sum, (long long)COUNT * (COUNT + 1) / 2);
}
```

运行结果：正确版本（release/acquire）在 ThreadSanitizer 下**没有报告**，结果正确；用 `-DWRONG` 把所有内存序（memory order）改成 `relaxed` 之后，TSan **报告数据竞争（data race）**，并指出了读 `buf_` 的位置（消费者 `pop`）和之前写 `buf_` 的位置（生产者 `push`）：

```text
== 正确版本（release/acquire），ThreadSanitizer ==
sum=20000100000 期望=20000100000
== 错误版本（全部 relaxed），ThreadSanitizer（只显示报告的前几行）==
WARNING: ThreadSanitizer: data race (pid=PID)
  Read of size 4 at 0xADDR by thread T2:
    #0 SpscQueue<int, 1024ul>::pop(int&) spsc.cpp:33 (spsc_bad+0x15e0) (BuildId: f0a1f1043090872bbdf701a694051bda6e251ac9)
  Previous write of size 4 at 0xADDR by thread T1:
    #0 SpscQueue<int, 1024ul>::push(int const&) spsc.cpp:26 (spsc_bad+0x152b) (BuildId: f0a1f1043090872bbdf701a694051bda6e251ac9)
    #0 pthread_create ../../../../src/libsanitizer/tsan/tsan_interceptors_posix.cpp:1022 (libtsan.so.2+0x5ac1a) (BuildId: 2a13a7710e361d06f7babbea53065ca2be93f738)
```

这个实验有三点值得面试时说：

1. 错误版本在 x86 上**多半也能得到正确结果**——所以不能靠“跑了没问题”来判断无锁（lock-free）代码正确；ThreadSanitizer 是基于 happens-before 分析的，它能抓住没有同步关系的访问。
2. 在 ARM/POWER 这类弱内存序平台，错误版本会真的读到未写好的数据。
3. TSan 的限制：只能报告**这次执行里实际发生**的竞争；对 `std::atomic_thread_fence` 的支持有限（可能误报）；运行慢 5-15 倍，内存多几倍。

### 5.6 缓存一致性与伪共享

- CPU 以**缓存行（cache line）**（x86 上通常 64 字节）为单位在核心之间搬运数据。一致性协议（如 MESI）保证同一缓存行在同一时刻只有一个核心可以写：某个核心要写，必须让其他核心的副本失效。
- **伪共享（false sharing）**：两个线程写**不同的变量**，但这两个变量碰巧在同一条缓存行里，于是缓存行在两个核心之间来回“乒乓”，性能骤降，而且代码里完全看不出共享。
- 解决：把各线程独占写的数据放到不同的缓存行（`alignas(64)` 或填充（padding））；C++17 提供了 `std::hardware_destructive_interference_size`（推荐的“避免伪共享的最小偏移”）——但这个常量是编译器给的，在不同编译选项/CPU 下可能不一致，GCC 对在头文件接口里使用它会警告 ABI 风险，所以很多代码库直接硬编码 64（Apple M 系列是 128）。
- 反过来，**真共享**的数据（总是一起访问的）要放在一起，让它们占同一缓存行（`hardware_constructive_interference_size`）。

### 5.7 实验 8：伪共享到底有多慢

```cpp
// 实验 5：伪共享（false sharing）。4 个线程各自递增“自己的”计数器，互不共享数据，
// 但如果计数器挤在同一个缓存行（通常 64 字节）里，缓存一致性协议会让这一行在核心之间来回搬运。
#include <atomic>
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

struct Packed { std::atomic<long> v{0}; };                   // 相邻放置，8 字节一个
struct alignas(64) Padded { std::atomic<long> v{0}; };       // 每个独占一条缓存行

template <class C>
double run(int threads, long iters) {
  std::vector<C> c(threads);
  auto t0 = std::chrono::steady_clock::now();
  std::vector<std::thread> ts;
  for (int i = 0; i < threads; ++i)
    ts.emplace_back([&, i] { for (long k = 0; k < iters; ++k) c[i].v.fetch_add(1, std::memory_order_relaxed); });
  for (auto& t : ts) t.join();
  return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
}

int main() {
  const long N = 20'000'000;
  std::printf("sizeof(Packed)=%zu sizeof(Padded)=%zu，CPU 核数=%u\n", sizeof(Packed), sizeof(Padded), std::thread::hardware_concurrency());
  for (int th : {1, 2, 4}) {
    double a = run<Packed>(th, N), b = run<Padded>(th, N);
    std::printf("线程数 %d：紧挨着 %7.1f ms | 各占缓存行 %7.1f ms | 慢 %.1f 倍\n", th, a, b, a / b);
  }
}
```

运行结果：

```text
sizeof(Packed)=8 sizeof(Padded)=64，CPU 核数=4
线程数 1：紧挨着   115.0 ms | 各占缓存行   118.3 ms | 慢 1.0 倍
线程数 2：紧挨着  1001.1 ms | 各占缓存行   126.8 ms | 慢 7.9 倍
线程数 4：紧挨着  2426.2 ms | 各占缓存行   115.0 ms | 慢 21.1 倍
```

解读：单线程时两者一样快（118 ms 上下）；2 个线程，紧挨着的版本慢了约 8 倍；4 个线程，慢了约 20 倍。线程数增加，理想情况下每个线程的工作量不变（总耗时应该基本不变），而**紧挨着的版本的耗时随线程数大幅增长**——这就是缓存行（cache line）乒乓的典型特征。

### 5.8 实验 9：线程池与条件变量的正确写法

线程池（thread pool）是另一个常考的手写题。要点已经写在代码注释里：谓词 wait、关闭时在锁里置标志再 `notify_all`、任务在锁外执行、析构 join、`packaged_task` 把返回值和异常通过 `future` 传回去。

```cpp
// 实验 14：线程池 + 条件变量的正确写法，用 TSan 检查。
// 要点：1) wait 必须带谓词（防虚假唤醒和丢失唤醒）；2) 关闭时先置标志再 notify_all；3) 任务在锁外执行；
//       4) 析构要 join；5) 用 packaged_task + future 把返回值和异常带回调用方。
#include <condition_variable>
#include <cstdio>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>

class ThreadPool {
 public:
  explicit ThreadPool(unsigned n) { for (unsigned i = 0; i < n; ++i) workers_.emplace_back([this] { loop(); }); }
  ~ThreadPool() {
    { std::lock_guard<std::mutex> lk(m_); stop_ = true; }       // 先置标志（在锁里），再唤醒
    cv_.notify_all();
    for (auto& t : workers_) t.join();
  }
  template <class F, class... A>
  auto submit(F&& f, A&&... a) -> std::future<std::invoke_result_t<F, A...>> {
    using R = std::invoke_result_t<F, A...>;
    auto task = std::make_shared<std::packaged_task<R()>>(std::bind(std::forward<F>(f), std::forward<A>(a)...));
    auto fut = task->get_future();
    { std::lock_guard<std::mutex> lk(m_); if (stop_) throw std::runtime_error("pool stopped"); q_.push([task] { (*task)(); }); }
    cv_.notify_one();
    return fut;
  }
 private:
  void loop() {
    for (;;) {
      std::function<void()> job;
      {
        std::unique_lock<std::mutex> lk(m_);
        cv_.wait(lk, [this] { return stop_ || !q_.empty(); });   // 带谓词的 wait
        if (q_.empty()) return;                                    // stop_ 且已排空
        job = std::move(q_.front()); q_.pop();
      }
      job();                                                       // 锁外执行
    }
  }
  std::vector<std::thread> workers_; std::queue<std::function<void()>> q_;
  std::mutex m_; std::condition_variable cv_; bool stop_ = false;
};

int main() {
  ThreadPool pool(4);
  std::vector<std::future<long>> fs;
  for (int i = 1; i <= 8; ++i) fs.push_back(pool.submit([](int n) { long s = 0; for (int k = 1; k <= n * 100000; ++k) s += k; return s; }, i));
  long total = 0; for (auto& f : fs) total += f.get();
  std::printf("8 个任务的结果之和 = %ld\n", total);
  auto bad = pool.submit([]() -> int { throw std::runtime_error("任务里抛出的异常"); });
  try { bad.get(); } catch (const std::exception& e) { std::printf("异常通过 future 传回调用方：%s\n", e.what()); }
}
```

运行结果（在 ThreadSanitizer 下，没有报告）：

```text
8 个任务的结果之和 = 1020001800000
异常通过 future 传回调用方：任务里抛出的异常
```

常见追问：

- **为什么 `stop_` 要在锁里修改？** 如果不在锁里，可能出现：工作线程检查谓词（`stop_` 为 false、队列空）→ 主线程设置 `stop_` 并 `notify_all` → 工作线程才进入 `wait`——**丢失唤醒**，永远睡下去。在锁里修改能保证“检查谓词”和“进入 wait”是原子的。
- **任务里抛异常怎么办？** `packaged_task` 会捕获异常并存入 `future`，`get()` 时重新抛出（输出中的最后一行）。如果直接 `std::function` 里执行裸任务而异常逃逸，会终止工作线程（`std::terminate`）。
- **如何做任务窃取（work stealing）？** 每个线程一个双端队列，空闲时从别人队列的另一端偷；减少全局队列锁的竞争。
- **如何避免线程数过多？** 线程数一般 ≈ 核数（CPU 密集），I/O 密集可以更多；`std::thread::hardware_concurrency()`。

### 5.9 并发面试题与答案要点

**Q52. 什么是数据竞争（data race）？它和竞态条件（race condition）有何区别？**
数据竞争是语言定义的：没有同步的并发（concurrency）访问同一内存位置且至少一个是写；它是未定义行为（UB, undefined behavior）。竞态条件是逻辑错误：结果依赖线程调度的时序（即使每次访问都是原子的，比如两个线程各自“检查再操作”）。没有数据竞争也可能有竞态条件；有数据竞争一定是错的。

**Q53. `std::atomic` 的 `memory_order` 有哪些？`relaxed`、`acquire/release`、`seq_cst` 的区别？**
见 5.3 的表。重点是 synchronizes-with 的“发布-获取”和 `seq_cst` 的全局顺序。实验 6 展示了 `release/acquire` 不足以禁止 store→load 重排。

**Q54. 解释 happens-before。**
同一线程内按程序顺序是 sequenced-before；跨线程通过 synchronizes-with（release 写被 acquire 读到、解锁/加锁、线程创建/join 等）建立；传递性。如果 A happens-before B，则 A 的结果对 B 可见；若两个访问之间没有 happens-before 且有一个是写，就是数据竞争。

**Q55. 写一个无锁（lock-free）的 SPSC 队列，并解释每个内存序（memory order）为什么这样选。**
见实验 7：下标自读用 relaxed；发布用 release；观察对方的下标用 acquire；把 `head`/`tail`/缓冲区分在不同缓存行（cache line）；为什么不需要 CAS（单生产者单消费者各自独占一个下标）。追问：改成 MPSC 或 MPMC 需要什么？答：CAS 竞争、ABA、每个槽位的序号（Vyukov 的有界队列用每槽序号避免锁）、内存回收。

**Q56. 什么是 ABA 问题？怎么解决？**
见 5.3。

**Q57. `compare_exchange_weak` 和 `strong` 的区别？**
`weak` 允许在值相等时也虚假失败（在 LL/SC 架构如 ARM 上更高效），所以要放在循环里；`strong` 在值相等时不会失败。不在循环里的单次 CAS 用 `strong`。失败时 `expected` 会被更新为当前值。

**Q58. 什么是伪共享（false sharing）？怎么检测和解决？**
见 5.6。检测：`perf c2c`（Linux）、性能计数器看缓存行失效；线程数增加反而更慢的症状；解决：对齐（alignment）/填充（padding）；把线程私有的数据聚集成线程本地结构；按线程分片计数器再汇总。

**Q59. 条件变量（condition variable）为什么必须用谓词？**
虚假唤醒（spurious wakeup）；通知可能先于等待（丢失唤醒）；多个等待者被唤醒后条件可能已经被别人消耗。`wait(lock, pred)` 内部循环检查。

**Q60. 双重检查锁（DCLP）为什么在旧标准下有问题？现在怎么写？**
旧写法：第一次检查指针（无锁）→ 加锁 → 再检查 → 构造并赋值。问题：赋值给指针可能先于对象构造完成被其他线程看到（重排序（reordering）），读到未构造完成的对象。C++11 之后：用原子指针 + acquire/release，或更简单地用魔法静态/`std::call_once`。

**Q61. `std::mutex` 和 `std::atomic` 哪个更快？什么时候用哪个？**
无竞争时，原子操作（atomic operation）远快于互斥量；但原子操作不能保护多变量不变式。需要保护涉及多个变量的临界区，用锁；只有一个独立计数器/标志，用原子。高竞争下两者都会差，要改变设计（分片、批处理、线程本地聚合）。

**Q62. 如何设计一个线程安全的队列？有锁和无锁各有什么取舍？**
有锁：互斥量 + 条件变量，简单、正确、吞吐在低到中等竞争下足够；无锁/等待自由：延迟更稳定、避免优先级反转和被抢占的线程持锁，但复杂度高、内存回收难、在高竞争下不一定更快。先用有锁版本，用数据证明瓶颈再改。

**Q63. 解释 `std::shared_mutex`（读写锁）的适用场景和陷阱。**
读多写少且读临界区较长时有益；读临界区很短时，读写锁本身的原子操作开销可能比互斥量更大；写者饥饿取决于实现；不支持升级锁（读锁升写锁会死锁（deadlock））。

**Q64. 线程安全的单例怎么写？**
C++11 起：`static T& instance() { static T t; return t; }`（魔法静态，线程安全）。注意：初始化顺序问题（析构顺序，在 `main` 退出后其他静态对象析构时还访问它）；可用“泄漏的单例”（`static T* p = new T;`）避免析构顺序问题。

**Q65. `std::async`、`std::thread`、`std::promise/future` 怎么选？**
`std::thread` 是最底层的；`promise/future` 用于一次性传递结果或异常；`std::async` 方便但返回的 future 析构会阻塞、线程管理不透明，工程里常用自己的线程池（thread pool）/执行器。C++26 的 `std::execution`（发送者/接收者）是新的异步框架（我没有验证）。

**Q66. 如何调试多线程问题？**
ThreadSanitizer（数据竞争、死锁检测）、Helgrind；日志加线程号和时间戳；`gdb` 的 `thread apply all bt` 看死锁时各线程栈；`rr`（记录并重放，确定性地复现竞态）；在压测中随机注入延迟（chaos）放大时序窗口。

**Q67. `volatile` 在多线程里有用吗？**
没用于同步。它不保证原子性，也不建立 happens-before，也不阻止 CPU 重排序。只用于告诉编译器“每次访问都要真的做”（内存映射 I/O，信号处理里的 `volatile sig_atomic_t`）。

**Q68. 什么是 RCU / hazard pointer？为什么需要？**
无锁数据结构里读者不加锁地遍历，写者不能立刻释放被替换的节点。hazard pointer：读者发布“我正在访问这个指针”；写者回收前检查没有读者发布过它。RCU/epoch：读者在读侧临界区内，写者等待所有读者都离开了旧的“纪元”后再回收。都解决无锁结构的安全内存回收问题。

---

## 六、未定义行为、优化与 sanitizer

### 6.1 为什么 UB 是高级面试的必考题

C++ 把“**程序员保证某些事不发生**”作为性能的基础：不检查数组越界、不检查空指针、假设有符号整数不溢出。违反这些约定就是**未定义行为（undefined behavior, UB）**——标准对此不规定任何结果。关键是：**UB 不是“结果不确定”，而是“整个程序的行为都没有意义”**；编译器可以假设 UB 永远不会发生，并据此做优化，包括把你的检查代码整个删掉。

三个相近的术语要分清：
- **未定义行为**：标准不规定任何要求（数组越界、有符号溢出、解引用空指针、数据竞争（data race）、违反严格别名（strict aliasing）、修改 const 对象……）。
- **未指定行为（unspecified）**：标准给出几种允许的结果，实现可以任选，且不需要文档化（函数实参的求值顺序、`std::vector` 的扩容倍数）。
- **实现定义行为（implementation-defined）**：实现必须选一种并写进文档（`sizeof(int)`、右移负数在C++20之前、`char` 是否有符号）。

### 6.2 常见 UB 清单

1. 有符号整数溢出（无符号溢出是回绕，定义良好）。
2. 越界访问数组/容器（`operator[]` 不检查）；迭代器失效（iterator invalidation）后使用。
3. 解引用空指针或悬空指针（dangling pointer）；释放后使用；二次释放。
4. 使用未初始化的变量（读取不确定值）。
5. 数据竞争（data race）。
6. 违反**严格别名规则（strict aliasing）**：通过不兼容类型的指针读写同一对象（例外：`char`/`unsigned char`/`std::byte` 可以别名任何对象）。类型双关（type punning）要用 `memcpy` 或 `std::bit_cast`（片段 G）。
7. 对象生命周期外访问；违反 `const`（修改原本声明为 const 的对象）。
8. 在构造/析构中调用纯虚函数（virtual function）。
9. 违反 ODR（单一定义规则）：不同翻译单元（translation unit）里同名的类/内联（inlining）函数定义不同。通常不报错，难以排查。
10. 移位量大于等于类型宽度或为负；除以零。
11. 函数声明有返回类型但没有 `return`（流程走到结尾）。
12. `noexcept` 函数抛出异常（会调用 `std::terminate`，这是定义好的，不是 UB，但常被误解）。

### 6.3 实验 10a：同一个程序，不同优化级别，不同答案

```cpp
// 实验 6a：未定义行为（UB）会被编译器“利用”。
// 有符号整数溢出是 UB，编译器可以假设它不会发生。下面这个函数在 -O0 下按机器行为回绕，
// -O2 下编译器认为 n+10 不可能比 n 小，直接把循环次数当作 10。
#include <climits>
#include <cstdio>

__attribute__((noinline)) int count_steps(int n) {
  int c = 0;
  for (int i = n; i < n + 10; ++i) ++c;   // n 接近 INT_MAX 时，n + 10 溢出
  return c;
}
__attribute__((noinline)) int count_steps_unsigned(unsigned n) {   // 无符号回绕有明确定义
  int c = 0;
  for (unsigned i = n; i < n + 10; ++i) ++c;
  return c;
}

int main() {
  std::printf("count_steps(INT_MAX - 5)           = %d\n", count_steps(INT_MAX - 5));
  std::printf("count_steps_unsigned(UINT_MAX - 5) = %d\n", count_steps_unsigned(UINT_MAX - 5));
}
```

运行结果（实验 10 的整体输出，前半部分）：

```text
-- g++ -O0 --
count_steps(INT_MAX - 5)           = 0
count_steps_unsigned(UINT_MAX - 5) = 0
-- g++ -O2 --
count_steps(INT_MAX - 5)           = 10
count_steps_unsigned(UINT_MAX - 5) = 0
-- g++ -O2 -fsanitize=undefined --
ub_optimize.cpp:9:21: runtime error: signed integer overflow: 2147483642 + 9 cannot be represented in type 'int'
count_steps(INT_MAX - 5)           = 0
count_steps_unsigned(UINT_MAX - 5) = 0
-- ASan：vector 扩容后使用旧指针 --
==PID==ERROR: AddressSanitizer: heap-use-after-free on address 0xADDR at pc 0xADDR bp 0xADDR sp 0xADDR
READ of size 4 at 0xADDR thread T0
    #0 0xADDR in main asan_demo.cpp:18
freed by thread T0 here:
    #8 0xADDR in main asan_demo.cpp:16
previously allocated by thread T0 here:
-- ASan：string_view 悬空 --
==PID==ERROR: AddressSanitizer: heap-use-after-free on address 0xADDR at pc 0xADDR bp 0xADDR sp 0xADDR
READ of size 1 at 0xADDR thread T0
```

- `count_steps(INT_MAX - 5)`：循环 `for (int i = n; i < n + 10; ++i)` 在 `n` 接近 `INT_MAX` 时，`n + 10` 溢出。**`-O0` 返回 0**（机器真的回绕成负数，条件一开始就不成立），**`-O2` 返回 10**（编译器认为 `n + 10` 一定大于 `n`，循环必然执行 10 次，直接返回常量）。Clang 的 `-O2` 同样返回 10。
- 无符号版本在所有优化级别都是 0：无符号回绕有明确定义，`n + 10` 回绕后确实小于 `n`。
- 加上 `-fsanitize=undefined`，UBSan 在运行时报告：`signed integer overflow: 2147483642 + 9 cannot be represented in type 'int'`——并且这个版本的结果又变回 0（插入了检查，改变了优化）。

**这个实验是回答“UB 会造成什么”最有说服力的例子**：不是崩溃，而是“不同优化级别得到不同答案”，而且“加了检查程序行为又变了”。

另一类常见的、被 UB 优化“吃掉”的代码：

- `if (p == nullptr) return;` 写在已经解引用 `p` 之后，编译器可以认为 `p` 非空，删除这个检查。
- `if (x + 1 < x) overflow();`（想用来检测溢出）：对有符号 `x` 会被删除。正确做法：先检查 `x == INT_MAX`，或用 `__builtin_add_overflow`（GCC/Clang），C++26 有 `std::add_sat` 等函数（C++26 的我没有验证）。

### 6.4 实验 10b：AddressSanitizer 抓“释放后使用”

```cpp
// 实验 6b：AddressSanitizer 抓“释放后使用”和“越界”。用法：g++ -fsanitize=address -g
#include <cstdio>
#include <string_view>
#include <string>
#include <vector>

int main(int argc, char**) {
  if (argc > 2) {   // 第 2 个演示：string_view 悬空
    std::string_view sv;
    { std::string tmp(100, 'x'); sv = tmp; }
    std::printf("%c\n", sv[0]);
    return 0;
  }
  std::vector<int> v{1, 2, 3};
  int* p = &v[0];
  v.push_back(4);        // 可能重新分配，p 悬空（迭代器/指针失效）
  v.push_back(5);
  std::printf("%d\n", *p);   // 释放后使用
}
```

实验 10 输出的后半部分已经包含了 ASan 的报告：`heap-use-after-free`，指出了读取发生的位置（`asan_demo.cpp:18`）、内存是在哪里被释放的（`vector::push_back` 触发的扩容释放了旧缓冲区，位置 `asan_demo.cpp:16`）、以及是在哪里分配的。第二个演示（`string_view` 指向已销毁的 `std::string`）同样被抓到。

### 6.5 工具箱

| 工具 | 抓什么 | 备注 |
|---|---|---|
| ASan（`-fsanitize=address`） | 越界、释放后使用、二次释放、栈/全局越界、泄漏（LSan） | 约 2 倍慢，内存多 2–3 倍 |
| UBSan（`-fsanitize=undefined`） | 有符号溢出、移位、空指针、对齐（alignment）、类型转换等 | 开销小，可用于测试环境长期开启 |
| TSan（`-fsanitize=thread`） | 数据竞争（data race）、死锁（deadlock，锁序反转） | 5–15 倍慢；不能与 ASan 同时用 |
| MSan（Clang 的 `-fsanitize=memory`） | 使用未初始化内存 | 需要整个程序（含标准库）都插桩 |
| Valgrind | 内存错误、泄漏（不用重新编译） | 20–50 倍慢 |
| 编译器警告 | `-Wall -Wextra -Wconversion -Wshadow -Wold-style-cast`；`-Werror` | 最便宜的静态检查 |
| 静态分析 | clang-tidy、cppcheck、编译器的 `-fanalyzer`（GCC） | 补充，不替代测试 |
| 标准库断言 | `-D_GLIBCXX_ASSERTIONS`（libstdc++）、`_LIBCPP_HARDENING_MODE`（libc++） | 给 `operator[]`、`front()` 等加边界检查，开销小 |
| 加固选项 | `-fstack-protector-strong`、`-D_FORTIFY_SOURCE=2/3`、`-fPIE -pie`、`-Wl,-z,relro,-z,now` | 生产环境减少漏洞可利用性 |

**CI 里的最佳实践**：同一套测试分别在 ASan+UBSan、TSan 下各跑一遍；模糊测试（libFuzzer / AFL）配 ASan。

### 6.6 评估顺序：一个常被问的“未指定行为”

函数实参的求值顺序是**未指定**的。实验 17 的第 9 项把三个 `next_id()` 调用放在同一个 `printf` 里：**g++ 输出 `103 102 101`，clang++ 输出 `101 102 103`**——同一份源码，两个编译器，不同的结果。C++17 规定了一些顺序（`a.b()`、`a << b`、`a = b` 的右到左等，以及 `new` 表达式），但**函数实参之间的求值顺序仍然未指定**（只保证不交叉，C++17 起每个实参的求值完全在另一个之前或之后）。`i = i++ + 1` 之类的在 C++11 之前是未定义，C++17 起好多已经有了定义，但不要写这种代码。

### 6.7 UB 面试题与答案要点

**Q69. 什么是未定义行为？为什么 C++ 允许 UB？**
见 6.1。允许 UB 是为了不为不需要的检查付费：编译器可以假设某些情况不发生，从而生成更快的代码；代价是把正确性的责任交给程序员。

**Q70. 有符号整数溢出为什么是 UB 而无符号不是？**
历史上不同机器用不同的表示（补码、反码、符号位），溢出行为不同，所以标准不定义；无符号被规定为模 2^N 回绕。现代编译器利用有符号溢出的 UB 来优化循环（比如假设归纳变量不溢出而向量化）。C++20 规定了有符号整数是补码，但**溢出依然是 UB**。

**Q71. 给一个“编译器利用 UB 优化”的例子。**
实验 10a：`-O0` 与 `-O2` 对同一函数给出 0 和 10。另一个例子：已经解引用的指针后面的空检查被删除。

**Q72. 什么是严格别名（strict aliasing）规则？怎么安全地做类型双关（type punning）？**
通过一种类型的左值（lvalue）访问另一种不兼容类型的对象是 UB（`char` 类型例外）；优化器据此假设 `int*` 与 `float*` 不会指向同一块内存，从而重排读写。安全做法：`std::memcpy`（编译器会优化成一条加载指令）、`std::bit_cast`（C++20，且是 constexpr）；union 双关在 C++ 里是 UB（虽然 GCC/Clang 当作扩展支持）。

**Q73. `std::vector::operator[]` 越界会发生什么？`at()` 呢？**
`operator[]` 越界是 UB；`at()` 抛 `std::out_of_range`。可以用 `-D_GLIBCXX_ASSERTIONS` 让 `operator[]` 在越界时直接终止程序，开销很小。

**Q74. 如何用工具发现 UB？**
见 6.5：ASan + UBSan + TSan 的组合，加上警告和静态分析，并且在 CI 持续运行；模糊测试能发现测试没覆盖的路径。

**Q75. `int x; std::cout << x;` 是 UB 吗？`unsigned char` 呢？**
读取未初始化的 `int` 是 UB（C++ 里"不确定值"的使用）。例外：读 `unsigned char`/`std::byte` 的不确定值在 C++ 里是允许的，用于访问原始存储。实际中，只要用到未初始化的值，优化器可能给出任何结果；MSan 能抓到。

**Q76. 移位操作什么时候是 UB？**
移位量是负数或大于等于左操作数类型的位宽；C++20 之前左移负数/移出符号位也是 UB（C++20 起左移按补码定义，但移位量规则不变）。

**Q77. ODR 违反是什么？为什么难排查？**
同一个实体（类、内联（inlining）函数、模板）在不同翻译单元（translation unit）里的定义不一致（比如两个 .cpp 里都有一个同名的非 static 的 `struct Config`，成员不同；或编译选项不同导致 `#ifdef` 展开不同）。链接器（linker）不检查，运行时表现为随机崩溃。排查：`-Wodr`（GCC，配合 LTO）、统一编译选项、匿名命名空间（namespace）。

**Q78. 如何写出对 UB 有防御的代码（比如检查加法是否溢出）？**
在运算**之前**检查范围（`if (a > INT_MAX - b)`），或使用 `__builtin_add_overflow`，或用更宽类型/饱和算术；不要事后检查结果。


---

## 七、异常、错误处理与异常安全

### 7.1 为什么异常是个有争议的话题

C++ 异常把错误处理从正常路径中分离出来，并且配合 RAII 自动清理。但它也引起了持续的争论：谷歌的内部风格指南禁用异常，很多低延迟、嵌入式、游戏代码库用 `-fno-exceptions`；而标准库本身（`bad_alloc`、`at()`、`string` 的构造）和大量应用代码依赖异常。面试官想确认：**你知道它的成本在哪，也知道怎么写出异常安全（exception safety）的代码**。

### 7.2 异常的实现与成本

- 主流平台（Itanium ABI）使用**表驱动、“零开销”模型**：编译器为每个函数生成描述“哪个指令范围里有哪些需要清理/捕获”的表，**不抛异常时，正常路径上没有额外指令**；抛出时，运行时查表、两阶段展开（先搜索处理者，再逐层清理）。
- 代价转移到了**抛出路径**：分配异常对象、查表、栈展开（stack unwinding），通常比普通函数返回慢**几个数量级**；并且让二进制变大（异常表、`.eh_frame`），阻碍某些优化。
- **MSVC x64** 同样基于表，但实现不同；x86 32 位用的是基于栈链表的模型，正常路径有开销。

### 7.3 实验 11：异常安全与异常的真实开销

```cpp
// 实验 12：异常安全与异常的真实开销。
#include <chrono>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

// --- 强异常保证：先在副本上做，最后用不会抛的 swap 提交（copy-and-swap）---
class Buffer {
  char* p_; size_t n_;
 public:
  static inline int fail_after = -1;   // 测试用：第 fail_after 次分配时抛异常
  static char* alloc(size_t n) { if (fail_after == 0) throw std::bad_alloc(); if (fail_after > 0) --fail_after; return new char[n]; }
  Buffer(const char* s) : p_(alloc(std::strlen(s) + 1)), n_(std::strlen(s)) { std::memcpy(p_, s, n_ + 1); }
  Buffer(const Buffer& o) : p_(alloc(o.n_ + 1)), n_(o.n_) { std::memcpy(p_, o.p_, n_ + 1); }
  Buffer(Buffer&& o) noexcept : p_(std::exchange(o.p_, nullptr)), n_(std::exchange(o.n_, 0)) {}
  ~Buffer() { delete[] p_; }
  void swap(Buffer& o) noexcept { std::swap(p_, o.p_); std::swap(n_, o.n_); }
  // 强保证：参数按值传递（拷贝可能抛，但此时 *this 还没动），然后 noexcept 的 swap
  Buffer& operator=(Buffer o) noexcept { swap(o); return *this; }
  // 对比：不安全的赋值——先释放旧的，再分配新的；分配失败时对象已损坏
  void bad_assign(const char* s) { delete[] p_; p_ = nullptr; n_ = 0; p_ = alloc(std::strlen(s) + 1); n_ = std::strlen(s); std::memcpy(p_, s, n_ + 1); }
  const char* c_str() const { return p_ ? p_ : "(null：对象已损坏)"; }
};

// --- 异常 vs 返回码 的成本 ---
__attribute__((noinline)) int thrower(int x, bool fail) { if (fail) throw std::runtime_error("x"); return x + 1; }
__attribute__((noinline)) int coder(int x, bool fail, int* out) { if (fail) return -1; *out = x + 1; return 0; }

int main() {
  std::puts("== 强异常保证 ==");
  { Buffer a("hello"), b("world"); Buffer::fail_after = 0;
    try { a = b; } catch (...) { std::printf("copy-and-swap 赋值：拷贝参数时分配失败，a 仍为 \"%s\"\n", a.c_str()); }   // 抛异常发生在按值参数的拷贝里，此时 a 还没被改动
    Buffer::fail_after = -1; }
  { Buffer a("hello"); Buffer::fail_after = 0;
    try { a.bad_assign("world"); } catch (...) { std::printf("先释放后分配的赋值，分配失败：a 变成 %s\n", a.c_str()); }
    Buffer::fail_after = -1; }

  std::puts("== 异常的开销：正常路径 vs 抛出路径 ==");
  const int N = 20'000'000;
  auto t0 = std::chrono::steady_clock::now(); long s = 0;
  for (int i = 0; i < N; ++i) { try { s += thrower(i, false); } catch (...) {} }
  double ok_exc = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / N;
  t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < N; ++i) { int o; if (coder(i, false, &o) == 0) s += o; }
  double ok_code = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / N;
  const int M = 200'000;
  t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < M; ++i) { try { s += thrower(i, true); } catch (...) { ++s; } }
  double fail_exc = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / M;
  t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < M; ++i) { int o; if (coder(i, true, &o) != 0) ++s; }
  double fail_code = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / M;
  std::printf("不出错时：try/catch 包裹的调用 %.2f ns/次，返回码 %.2f ns/次（几乎没有差别：零开销模型）\n", ok_exc, ok_code);
  std::printf("出错时  ：抛异常 %.0f ns/次，返回码 %.2f ns/次（异常慢 %.0f 倍，所以别把异常用作常规控制流）\n", fail_exc, fail_code, fail_exc / (fail_code > 0.01 ? fail_code : 0.01));
  if (s == 42) std::puts("");
}
```

运行结果：

```text
== 强异常保证 ==
copy-and-swap 赋值：拷贝参数时分配失败，a 仍为 "hello"
先释放后分配的赋值，分配失败：a 变成 (null：对象已损坏)
== 异常的开销：正常路径 vs 抛出路径 ==
不出错时：try/catch 包裹的调用 0.62 ns/次，返回码 0.89 ns/次（几乎没有差别：零开销模型）
出错时  ：抛异常 1323 ns/次，返回码 0.70 ns/次（异常慢 1883 倍，所以别把异常用作常规控制流）
```

解读：

1. **强异常保证**：copy-and-swap 赋值运算符（参数按值传递，先拷贝再 noexcept 地 swap），分配失败时 `a` 保持 `"hello"`；而“先释放旧资源再分配新资源”的朴素写法在分配失败后，对象已经损坏（`a` 变成空指针）。
2. **正常路径**：包着 `try/catch` 的调用和返回错误码的调用，每次约 0.6–0.9 ns，没有可测的差别——这就是“零开销”。
3. **抛出路径**：一次抛出并捕获约 1000+ ns，比返回码慢上千倍。所以：**异常用来表示真正的异常情况，不要用于常规控制流**（比如“找不到就抛”在热循环里）。

### 7.4 异常安全保证的四个级别

1. **无保证**：失败后程序处于未知状态，可能泄漏资源。
2. **基本保证（basic）**：失败后不泄漏资源、不破坏不变式，但对象状态可能改变（有效但未指定）。
3. **强保证（strong）**：要么成功，要么没有任何副作用（事务语义）。实现手法：先在副本上做，最后用不会抛的操作提交（copy-and-swap）。
4. **不抛保证（nothrow）**：`noexcept`。析构函数、`swap`、移动操作应当提供。

### 7.5 `noexcept` 的细节

- `noexcept` 是函数类型的一部分（C++17）；如果 `noexcept` 函数抛出异常，直接调用 `std::terminate`（**不展开栈**也可能不执行析构，由实现决定）。
- **析构函数默认是 `noexcept(true)`**。在栈展开（stack unwinding）期间如果析构函数又抛出异常且没有被捕获，程序终止。所以析构函数里不要让异常逃逸；需要可能失败的清理，提供显式的 `close()` 函数，析构里吞掉异常。
- 条件 `noexcept`：`void swap(T& a, T& b) noexcept(noexcept(a.swap(b)))`；`noexcept(expr)` 运算符在编译期（compile time）检查表达式是否不抛。
- `std::move_if_noexcept`、`std::is_nothrow_move_constructible` 依赖它（见第二章 vector 扩容）。
- 构造函数中抛出异常：已构造的成员和基类会被析构，对象本身的析构函数**不会**被调用——所以成员应当用 RAII 类型管理资源，而不是在构造函数里手工 `new` 然后 `delete` 在析构里（构造到一半抛了就泄漏）。
- **catch 要按（const）引用**：按值捕获多态（polymorphism）异常会发生切片；`throw;` 重新抛出当前异常保持原类型，`throw e;` 会拷贝并切片。
- `std::exception_ptr` 可以把异常跨线程传递（`promise::set_exception`、线程池（thread pool）里的 `future`）。
- **异常跨越动态库（shared library）边界**：要求两边使用同一个 C++ 运行库、兼容的 ABI；跨 C 接口（`extern "C"` 函数）抛出异常是未定义行为（UB, undefined behavior），要在边界处捕获并转成错误码。

### 7.6 其他错误处理方式

| 方式 | 适用 | 注意 |
|---|---|---|
| 返回码 / `std::error_code` | 错误常见、需要快速路径 | 调用方可能忘了检查（`[[nodiscard]]` 能强制） |
| `std::optional<T>` | “可能没有值”但不关心原因 | 不带错误信息 |
| `std::expected<T, E>`（C++23） | 返回值或错误，带 monadic 操作 | 片段 E 验证了用法：`transform`/`and_then`/`value_or` |
| 异常 | 真正的异常、构造函数失败、深层调用栈的错误传播 | 抛出慢；二进制变大 |
| 断言 / 契约 | 违反前置条件（程序员错误） | 调试版检查；C++26 契约（未验证）|

### 7.7 异常面试题与答案要点

**Q79. 异常的开销是什么？为什么说“零开销”？**
见 7.2 和实验 11：正常路径没有额外指令，抛出路径慢几个数量级，二进制体积增加。

**Q80. 析构函数里抛异常会怎样？**
默认 `noexcept`，抛出会 `std::terminate`；在栈展开（stack unwinding）时抛出第二个异常同样终止。设计：析构里捕获并记录/吞掉，提供显式 `close()` 让调用方处理错误。

**Q81. 构造函数里可以抛异常吗？抛了之后资源怎么办？**
可以，这是构造失败的标准报告方式。已构造的子对象会被析构，但本对象的析构函数不会被调用，所以每个资源都应该由独立的 RAII 成员持有。

**Q82. 什么是 copy-and-swap？它给出什么保证？**
实验 11：拷贝构造出副本（可能抛，但还没碰 `*this`），然后用 noexcept 的 `swap` 交换。提供强异常保证；还天然处理自赋值；代价是多一次拷贝（有时可以用更高效的专门实现）。

**Q83. `noexcept` 对性能的意义？**
让标准库可以选择移动而不是拷贝（vector 扩容）；让编译器省略异常展开所需的代码；但是**不要随意给可能抛的函数加 `noexcept`**，因为抛出时会直接终止。

**Q84. 如何在不用异常的代码库里报告构造失败？**
两阶段初始化（先构造空对象再 `init()` 返回错误码）、工厂函数返回 `std::optional`/`std::expected`、静态 `create()` 并把构造函数设为私有。

**Q85. `throw;` 和 `throw e;` 有什么区别？**
前者重新抛出当前处理的异常对象，保持动态类型；后者抛出 `e` 的拷贝，类型是 `e` 的静态类型，可能切片。

---

## 八、标准库内部与性能

### 8.1 为什么要懂 STL 内部

标准库只规定了接口和复杂度，没有规定实现；但实现的细节决定了**你的代码在缓存（cache）里怎么跑**。高级面试常问：为什么 `std::vector` 通常比 `std::list` 快得多？`unordered_map` 在哪里分配内存？哪些操作会使迭代器失效（iterator invalidation）？

### 8.2 实验 12：容器的真实行为

```cpp
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
```

运行结果（libstdc++ 13 / x86-64；具体数字是实现细节）：

```text
== vector 的容量增长 ==
容量序列：1 2 4 8 16 32 64 128 256 512 1024 （libstdc++ 为 2 倍增长；MSVC 据说约 1.5 倍，这里没有验证）
shrink_to_fit 后地址发生了变化（只是请求，不保证）
== 迭代器/指针失效 ==
push_back 触发扩容后，旧指针 不再等于 新数据地址
list 插入不使已有迭代器失效，*it=1
deque 两端插入：旧元素的引用仍有效 *p=2（但迭代器会失效）
== std::string 的小字符串优化（SSO）==
sizeof(string)=32  空串 capacity=15
长度 16 开始使用堆内存（SSO 能放下 15 个字符 + 结尾 '\0'）
== unordered_map 的桶与重哈希 ==
max_load_factor=1.0；桶数增长：13(@0) 29(@13) 59(@29) 127(@59) 257(@127) 541(@257) 1109(@541) 2357(@1109) 
reserve(1000) 之后桶数=1031，插入 1000 个元素不再重哈希
重哈希后，元素的引用仍有效（节点式存储）：*p=1；但迭代器会失效
== 节点式容器的元素开销（估算）==
sizeof(std::pair<const int,int>)=8；map/unordered_map 每个节点还有指针、颜色或哈希缓存等簿记，实际每个元素远大于 8 字节
```

要点：

- **vector** 的容量增长序列是 1、2、4、8……（2 倍）。增长因子小于黄金比例（约 1.618）时，释放的旧内存块有机会被后续分配复用；大于它则不行——这是某些实现（MSVC 约 1.5 倍、Facebook folly 的 1.5 倍）选择较小因子的理由之一。（这是常见的说法，我没有在这里验证。）`shrink_to_fit` 只是请求。
- **迭代器/指针/引用失效**：`vector` 扩容时全部失效；`list` 和 `map` 的插入不使已有迭代器失效（iterator invalidation）；`deque` 两端插入使迭代器失效但不使对已有元素的引用失效（实验中旧元素的引用仍有效）；`unordered_map` 重哈希使迭代器失效，但对元素的引用/指针仍有效（因为是节点式存储）。
- **`std::string` 的 SSO**：libstdc++ 的 `sizeof(string)` 是 32，内联（inlining）缓冲区容纳 15 个字符 + 结尾 `\0`；长度达到 16 时开始使用堆。libc++ 的 `string` 据我所知是 24 字节、内联容量 22（未在这里验证）。**所以含短字符串的代码常常没有任何堆分配，而 `std::string` 大小超过 15/22 字符就会分配。**
- **`unordered_map`** 的桶数是质数序列（13、29、59、127……），`max_load_factor` 默认为 1.0，每个元素是独立的堆节点（`std::allocator` 的每个节点一次分配），所以缓存（cache）不友好；`reserve(n)` 可以一次性避免重哈希。需要更快的哈希表时，用开放寻址的实现（Abseil `flat_hash_map`、`boost::unordered_flat_map`、C++23 的 `std::flat_map` 是有序的另一种东西）。

### 8.3 迭代器失效速查

| 容器 | 插入 | 删除 |
|---|---|---|
| `vector` | 扩容时全部失效；否则插入点之后（含）失效 | 被删位置及之后失效 |
| `deque` | 中间插入全部失效；两端插入：迭代器失效（iterator invalidation），引用不失效 | 中间删除全部失效；两端删除只影响被删元素 |
| `list`/`forward_list` | 都不失效 | 只有被删元素失效 |
| `map`/`set` | 都不失效 | 只有被删元素失效 |
| `unordered_*` | 重哈希时迭代器失效，引用不失效 | 只有被删元素失效 |

（`erase` 之后用返回值作为下一个迭代器：`it = c.erase(it);`。）

### 8.4 缓存与分支预测：为什么“复杂度相同”的代码差几十倍

现代 CPU 的访存延迟：L1 约 1 ns 以内，L2 几 ns，L3 十几 ns，主存约 60–100 ns。**顺序访问连续内存时，硬件预取器能提前把数据拉进缓存（cache）；沿着指针链跳转时，每一次都可能是一次主存访问。**

### 8.5 实验 13：几个“凭直觉会猜错”的性能微基准

```cpp
// 实验 9：几个“凭直觉会猜错”的性能微基准。-O2。数字取决于机器，只看相对大小。
// 微基准容易被编译器优化掉或测错，这里用 asm volatile 阻止结果被删除；严肃测量请用 Google Benchmark。
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <functional>
#include <list>
#include <numeric>
#include <random>
#include <vector>

template <class F> double ms(F&& f) { auto t = std::chrono::steady_clock::now(); f(); return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t).count(); }
template <class T> inline void keep(T&& v) { asm volatile("" : : "g"(v) : "memory"); }

// --- 1. 分支预测 ---
long branchy(const std::vector<int>& a) {
  long s = 0;
  for (int r = 0; r < 20; ++r) for (int x : a) if (x >= 128) { s += x; asm volatile(""); }   // asm 防止编译器把分支改成无分支的 cmov/向量化
  return s;
}

// --- 2. 虚函数 / CRTP / std::function / 函数指针 ---
struct IShape { virtual ~IShape() = default; virtual int f(int) const = 0; };
struct Sq : IShape { int f(int x) const override { return x * 2 + 1; } };
struct Cu : IShape { int f(int x) const override { return x * 3 + 1; } };   // 第二个实现：编译器不能再推测只有一种动态类型
struct SqCRTP { int f(int x) const { return x * 2 + 1; } };
template <class D> struct Base { int call(int x) const { return static_cast<const D*>(this)->f(x); } };
struct Derived : Base<Derived> { int f(int x) const { return x * 2 + 1; } };
__attribute__((noinline)) int plain(int x) { return x * 2 + 1; }

int main() {
  std::mt19937 rng(1); std::vector<int> a(1 << 20); for (int& x : a) x = rng() % 256;
  keep(branchy(a));
  double unsorted = ms([&] { keep(branchy(a)); });
  std::sort(a.begin(), a.end());
  double sorted = ms([&] { keep(branchy(a)); });
  std::printf("[分支预测] 同一个循环：随机数据 %.1f ms，先排序 %.1f ms（%.1f 倍）\n", unsorted, sorted, unsorted / sorted);

  const int N = 1 << 20;
  std::vector<int> v2(N); std::iota(v2.begin(), v2.end(), 0);
  std::list<int> seq(v2.begin(), v2.end());                       // 节点按顺序分配，内存里大体相邻
  std::vector<int> r2 = v2; std::shuffle(r2.begin(), r2.end(), rng);
  std::list<int> scat(r2.begin(), r2.end()); scat.sort();          // sort 只重连指针：遍历顺序与内存位置无关
  double tv = ms([&] { long s = 0; for (int r = 0; r < 20; ++r) for (int x : v2) s += x; keep(s); });
  double tl = ms([&] { long s = 0; for (int r = 0; r < 20; ++r) for (int x : seq) s += x; keep(s); });
  double ts = ms([&] { long s = 0; for (int r = 0; r < 20; ++r) for (int x : scat) s += x; keep(s); });
  std::printf("[缓存局部性] 求和 %d 个 int：vector %.1f ms | list(节点相邻) %.1f ms | list(节点分散) %.1f ms（分散的比 vector 慢 %.0f 倍）\n", N, tv, tl, ts, ts / tv);

  const long K = 300'000'000;   // 每次调用的结果是下一次的输入，防止被向量化或算出闭式解
  Sq sq; Cu cu; IShape* ip = (rng() % 2) ? (IShape*)&sq : (IShape*)&cu; asm volatile("" : "+r"(ip));   // 运行时才知道动态类型
  Derived dd; SqCRTP cr; int (*fp)(int) = plain; asm volatile("" : "+r"(fp));
  std::function<int(int)> sf = [](int x) { return x * 2 + 1; };
  double t1 = ms([&] { int x = 1; for (long i = 0; i < K; ++i) x = ip->f(x); keep(x); });
  double t2 = ms([&] { int x = 1; for (long i = 0; i < K; ++i) x = dd.call(x); keep(x); });
  double t3 = ms([&] { int x = 1; for (long i = 0; i < K; ++i) x = fp(x); keep(x); });
  double t4 = ms([&] { int x = 1; for (long i = 0; i < K; ++i) x = sf(x); keep(x); });
  std::printf("[调用方式] %ld 次调用：虚函数 %.0f ms | CRTP(可内联) %.0f ms | 函数指针 %.0f ms | std::function %.0f ms\n", K, t1, t2, t3, t4);
  (void)cr;
}
```

运行结果（数字取决于机器，只看相对大小）：

```text
[分支预测] 同一个循环：随机数据 99.6 ms，先排序 7.9 ms（12.5 倍）
[缓存局部性] 求和 1048576 个 int：vector 6.7 ms | list(节点相邻) 65.2 ms | list(节点分散) 1731.8 ms（分散的比 vector 慢 259 倍）
[调用方式] 300000000 次调用：虚函数 404 ms | CRTP(可内联) 93 ms | 函数指针 405 ms | std::function 408 ms
```

解读：

1. **分支预测（branch prediction）**：同一个循环，数据随机时约 100 ms，先排序后约 8 ms（约 12 倍）。条件 `x >= 128` 在随机数据上是不可预测的，每次误判要冲刷流水线（十几到二十几个周期）；排序后分支先全不成立再全成立，预测几乎总是对的。注意：我在 if 里加了 `asm volatile("")`，因为**没加的时候编译器把这个分支改成了无分支的条件移动或向量化，排序前后没有差别**（我第一次运行就遇到了，0.9 倍）。这本身也是一个值得说的点：“分支预测”的实验很容易被优化器抹平。
2. **缓存局部性（cache locality）**：对 100 万个 `int` 求和（做 20 遍）：`vector` 约 7 ms；`list` 节点按顺序分配（内存里大体相邻）约 50-65 ms；**节点在内存中被打乱后（`list::sort` 只重连指针）约 1700 ms，是 `vector` 的两百多倍**。复杂度都是 O(n)，差的是缓存（cache）。
3. **调用方式**：每次调用的结果是下一次的输入（避免被向量化/算出闭式）。虚调用、函数指针、`std::function` 都约 400 ms（300M 次调用，每次约 1.3 ns）；**CRTP/可内联（inlining）的调用约 90 ms，快约 4 倍**。差别的主体不是“间接调用的两次读取”，而是**能不能内联**：内联后编译器还能做进一步优化。我第一次写这个实验时只有一个派生类，GCC 做了**投机性去虚拟化（devirtualization）**（推测只有这一个实现，加一个类型检查后内联），结果虚调用反而比函数指针快——加了第二个派生类、运行时才确定类型后，才得到上面的结果。**微基准（microbenchmark）测的往往是编译器，而不是你以为的东西。**

### 8.6 性能分析的方法论

- **先测量，再优化**。用 `perf record` + 火焰图（flame graph）、`perf stat`（看 IPC、缓存（cache）未命中、分支误预测）、Valgrind 的 `cachegrind`/`callgrind`、Intel VTune。
- **微基准（microbenchmark）的陷阱**：结果被优化掉（用 `benchmark::DoNotOptimize`/`asm volatile` 阻止）、测的是缓存热的最好情况、频率调节和噪声（固定 CPU 频率、绑核、多次取中位数/最小值）、只测了一个输入规模。
- **常见优化方向**（按收益排序大致是）：算法与数据结构 → 内存布局（数组结构 SoA vs 结构数组 AoS，紧凑、连续）→ 减少分配 → 减少拷贝 → 避免锁竞争与伪共享（false sharing） → 分支与内联（inlining） → SIMD。
- **编译器选项**：`-O2`/`-O3`、`-march=native`（只用于自己机器上跑的程序）、LTO（`-flto`）、PGO（`-fprofile-use`）。
- **数据导向设计（data-oriented design）**：按“访问模式”而不是“概念模型”组织数据。比如粒子系统里，位置数组和速度数组分开存放，遍历时只读用到的字段。
- **低延迟系统的通用做法**：热路径无分配、无锁（lock-free）或锁竞争最小、线程绑核（CPU affinity）、关闭超线程干扰、避免系统调用、预热缓存/页面（预先触碰内存）、`mlock` 防止换页、大页（hugepages）。

### 8.7 STL 与性能面试题与答案要点

**Q86. `std::vector` 的扩容策略？为什么是倍数增长？`reserve` 的作用？**
倍数增长使 `push_back` 的均摊复杂度是 O(1)；增长因子是实现细节（libstdc++ 2 倍，MSVC 约 1.5 倍，见实验 12）。已知大小时 `reserve` 避免多次重新分配和元素搬运。

**Q87. `unordered_map` 的实现和性能特征？**
链式哈希（桶 + 节点），指针追逐；重哈希时迭代器失效（iterator invalidation）；最坏复杂度 O(n)（哈希冲突攻击）；`reserve`；自定义哈希；替代：开放寻址的 flat 哈希表。

**Q88. `std::map` 是怎么实现的？和 `unordered_map` 怎么选？**
通常是红黑树，节点独立分配，插入删除查找 O(log n)，有序，迭代器稳定。需要有序遍历/范围查询用 map；只做查找用 unordered_map；小数据量时排序的 `vector` + 二分查找常常更快（C++23 `flat_map` 基于此）。

**Q89. `std::sort` 的实现和复杂度？`std::stable_sort` 呢？**
introsort：快排 + 当递归过深退化到堆排序（保证最坏 O(n log n)）+ 小区间用插入排序；不稳定。`stable_sort` 归并，稳定，需要额外内存（有则 O(n log n)，否则 O(n log² n)）。只要前 k 个用 `partial_sort`，只要第 k 个用 `nth_element`（平均 O(n)）。

**Q90. 为什么 `vector` 通常比 `list` 快得多？什么时候 `list` 反而合适？**
缓存局部性（cache locality，实验 13 的两百多倍）。`list` 的优势是：插入删除不使迭代器失效、已有迭代器指向的位置做 O(1) 的插入/删除/拼接（`splice`）。但即便如此，除非元素非常大或需要稳定的地址，通常也不如 `vector`。

**Q91. 什么是小字符串优化（SSO）？**
见实验 12：短字符串直接存在对象内部的缓冲区，避免堆分配。注意：SSO 使 `std::string` 的移动不保证“指针稳定”——移动后指向旧字符串内部缓冲区的 `data()` 指针/`string_view` 失效。

**Q92. 数组结构（SoA）和结构数组（AoS）？**
AoS：`struct P {float x,y,z,vx,vy,vz;}; vector<P>`；SoA：每个字段一个数组。只处理其中一部分字段、需要 SIMD 时 SoA 更好；经常一起访问全部字段、随机访问单个对象时 AoS 更好。

**Q93. 虚函数（virtual function）调用一定慢吗？怎么优化？**
慢的主要来源是间接分支预测（branch prediction）失败和无法内联（inlining）。优化：`final` 让编译器去虚拟化（devirtualization）；CRTP/模板静态多态（static polymorphism）；`std::variant` + `visit`（按类型分组处理）；按类型批量处理（把同类对象放在一起，使分支可预测）；PGO 让编译器做投机性去虚拟化。

**Q94. 如何降低 `std::function` 的开销？**
它有类型擦除（type erasure）的间接调用，可能堆分配（捕获较大时；SBO 阈值由实现决定）。热路径用模板参数传递可调用对象（可内联）、函数指针、`std::function_ref`（C++26，未验证）/自己写非拥有的轻量引用、或 `std::move_only_function`（C++23）。

**Q95. 什么是 `[[likely]]`/`[[unlikely]]`、`__builtin_expect`、PGO？**
给编译器分支概率提示，影响代码布局（把常见路径放在顺序执行路径上），但不改变语义。PGO 用真实运行数据驱动，一般比手写提示更准确。

**Q96. 为什么有时 `-O3` 反而比 `-O2` 慢？**
激进的内联与循环展开增加代码体积，导致指令缓存（cache）缺失；向量化引入开销（对短循环）；所以要实测。

---

## 九、现代 C++（17/20/23）：值得深入的特性

### 9.1 要点速览（每一项面试都可能问到“为什么”）

- **结构化绑定**：`auto [k, v] = *map_it;`，对 `tuple`、`pair`、聚合体、数组有效；绑定名是别名，不是新变量（引用性取决于 `auto&`）。
- **`std::optional`、`std::variant`、`std::any`**：`optional` 是“有或无”，`variant` 是类型安全的联合体（union，`std::visit` 访问；可能处于 `valueless_by_exception` 状态——赋值时构造抛异常会让它变成无值），`any` 是类型擦除（type erasure，有堆分配可能）。
- **`std::string_view` / `std::span`**：非拥有的视图。零拷贝，但要管生命周期。
- **Ranges 与视图（C++20）**：用管道 `|` 组合惰性的 `views::filter`/`transform`/`take`。视图是惰性的，在遍历时才计算；对临时容器调用 ranges 算法会返回 `std::ranges::dangling`，在编译期（compile time）阻止悬空迭代器（片段 I 验证）。注意视图的 `const` 迭代语义和缓存（cache，`filter_view` 的 `begin()` 会缓存，非 const 遍历）。
- **三路比较 `<=>`（C++20）**：`auto operator<=>(const T&) const = default;` 同时生成所有比较运算符。
- **Concepts / constexpr / consteval**：第三章。
- **`std::format`**（C++20）、`std::print`（C++23，据我所知 libstdc++ 14 起支持，本环境的 GCC 13 没有）：类型安全的格式化。
- **`std::expected`（C++23）、deducing this（显式对象形参）、`std::flat_map`、`std::mdspan`**：g++ 13 支持 `std::expected`（片段 E）和 deducing this；`flat_map` 要 libstdc++ 15 左右（我没有验证）。
- **模块（Modules，C++20）**：用 `import` 代替 `#include`，编译更快、没有宏泄漏。实际使用受限于构建系统（CMake、Ninja 的支持程度）和编译器成熟度，**生产代码库的采用仍然有限**（据我所知）。
- **C++26（我没有验证，只写方向）**：静态反射、契约、`std::execution`（发送者/接收者）、hazard pointer 与 RCU 等并发（concurrency）原语。

### 9.2 协程（Coroutines）

**为什么**：异步代码（网络、IO）用回调很难读（回调地狱），用状态机很难写。协程让你**用顺序的写法表达可以暂停和恢复的计算**。

**机制**：任何函数体里出现 `co_await`、`co_yield` 或 `co_return` 就是协程。编译器把它改写成：
1. 一个**协程帧**（coroutine frame）：保存局部变量、暂停点、promise 对象。**通常在堆上分配**（编译器有时可省略，但不能依赖）。
2. 一个 **promise_type**：控制协程行为——`get_return_object`（返回给调用者的对象）、`initial_suspend`/`final_suspend`（开始/结束时是否暂停）、`yield_value`、`return_value`/`return_void`、`unhandled_exception`。
3. **awaiter**：`co_await expr` 通过 `await_ready`（是否需要暂停）、`await_suspend`（暂停时做什么，如把句柄交给事件循环）、`await_resume`（恢复时的结果）控制。
4. **`std::coroutine_handle`**：可以 `resume()`、`destroy()` 的句柄。

C++20 只给了底层机制，没有给标准库的 `generator` 或 `task` 类型（`std::generator` 在 C++23 加入；`task` 类型要自己写或用库，如 cppcoro、Boost.Asio 的 awaitable、libunifex）。

### 9.3 实验 14：一个最小的 generator

```cpp
// 实验 10：C++20 协程的最小实现——一个 generator。
// 协程是“可以暂停和恢复的函数”。编译器把它改写成：堆上的协程帧（保存局部变量和暂停点）+ promise 对象 + 句柄。
// 这里重载 promise 的 operator new 来观察协程帧确实分配在堆上（编译器有时可以省略分配，但不能依赖）。
#include <coroutine>
#include <cstdio>
#include <exception>
#include <new>
#include <utility>

static int g_frame_allocs = 0; static size_t g_frame_bytes = 0;

template <class T>
class Generator {
 public:
  struct promise_type {
    T value;
    Generator get_return_object() { return Generator{std::coroutine_handle<promise_type>::from_promise(*this)}; }
    std::suspend_always initial_suspend() noexcept { return {}; }   // 创建后先挂起，等调用者来取值
    std::suspend_always final_suspend() noexcept { return {}; }     // 结束时不销毁帧，由 Generator 析构负责
    std::suspend_always yield_value(T v) noexcept { value = std::move(v); return {}; }
    void return_void() noexcept {}
    void unhandled_exception() { std::terminate(); }
    static void* operator new(size_t n) { ++g_frame_allocs; g_frame_bytes += n; return ::operator new(n); }
    static void operator delete(void* p) noexcept { ::operator delete(p); }
  };
  explicit Generator(std::coroutine_handle<promise_type> h) : h_(h) {}
  Generator(Generator&& o) noexcept : h_(std::exchange(o.h_, {})) {}
  Generator(const Generator&) = delete;
  ~Generator() { if (h_) h_.destroy(); }
  bool next() { h_.resume(); return !h_.done(); }
  const T& value() const { return h_.promise().value; }
 private:
  std::coroutine_handle<promise_type> h_;
};

Generator<long> fib(int n) {
  long a = 0, b = 1;
  for (int i = 0; i < n; ++i) { co_yield a; long t = a + b; a = b; b = t; }
}

int main() {
  std::printf("创建前 g_frame_allocs=%d\n", g_frame_allocs);
  auto g = fib(10);
  std::printf("创建协程后（函数体还没开始执行）：协程帧分配 %d 次，%zu 字节\n", g_frame_allocs, g_frame_bytes);
  std::printf("前 10 个斐波那契数：");
  while (g.next()) std::printf("%ld ", g.value());
  std::puts("");
}
```

运行结果：

```text
创建前 g_frame_allocs=0
创建协程后（函数体还没开始执行）：协程帧分配 1 次，88 字节
前 10 个斐波那契数：0 1 1 2 3 5 8 13 21 34 
```

解读：创建协程（coroutine）时（函数体还没开始执行）就有**一次堆分配，88 字节**——这就是协程帧（coroutine frame）；`initial_suspend` 返回 `suspend_always`，所以调用 `fib(10)` 只是创建了帧和 promise，并没有执行函数体。每次 `next()` 恢复协程直到下一个 `co_yield`。常见追问：协程相比线程的成本？（协程帧一次分配，切换是普通函数调用级别，无内核参与；但也没有并行。）生命周期风险？（协程帧里保存的引用参数可能在协程恢复时已经悬空（dangling），比如按引用传入的临时对象——协程参数默认按值拷贝进帧，**引用参数不会延长被引用对象的生命周期**。）

### 9.4 类型擦除：`std::function` 是怎么做到的

**为什么**：想把“任何可调用的东西”放进同一种类型（回调、任务队列），但不想要求它们继承同一个基类。办法：外层是普通的值语义类，里面持有**抽象基类指针**，具体类型被藏在一个**模板派生类**里；再加上**小对象优化（SBO）**，让小的可调用对象直接放在内部缓冲区而不是堆上。

### 9.5 实验 15：手写一个带 SBO 的 `Function`

```cpp
// 实验 15：类型擦除（type erasure）——std::function 的原理。
// 目标：把“任何可以被调用的东西”装进同一个类型里，调用方不需要知道具体类型，也不需要继承关系。
// 做法：外层是普通类（值语义），内部持有一个抽象基类指针，具体类型在模板派生类里。
// 再加一个“小对象优化”：足够小的可调用对象直接放在内部缓冲区，避免堆分配。
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>
#include <string>
#include <type_traits>
#include <utility>

static int g_allocs = 0;
void* operator new(std::size_t n) { ++g_allocs; if (void* p = std::malloc(n)) return p; throw std::bad_alloc(); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

template <class Sig> class Function;
template <class R, class... A>
class Function<R(A...)> {
  struct Concept {
    virtual R call(A...) = 0;
    virtual Concept* clone(void* buf) const = 0;          // buf 为空 -> 堆上拷贝
    virtual Concept* move_to(void* buf) noexcept = 0;     // 把自己搬到 buf（用于内联存储的搬迁）
    virtual ~Concept() = default;
  };
  template <class F> struct Model final : Concept {
    F f;
    explicit Model(F f) : f(std::move(f)) {}
    R call(A... a) override { return f(std::forward<A>(a)...); }
    Concept* clone(void* buf) const override { return buf ? new (buf) Model(f) : new Model(f); }
    Concept* move_to(void* buf) noexcept override { return new (buf) Model(std::move(f)); }
  };
  static constexpr size_t kSmall = 32;
  alignas(std::max_align_t) unsigned char buf_[kSmall];
  Concept* p_ = nullptr;
  bool inline_ = false;
  void reset() noexcept { if (p_) { if (inline_) p_->~Concept(); else delete p_; p_ = nullptr; } }
 public:
  Function() = default;
  template <class F> Function(F f) {
    if constexpr (sizeof(Model<F>) <= kSmall && alignof(Model<F>) <= alignof(std::max_align_t) && std::is_nothrow_move_constructible_v<F>) {
      p_ = new (buf_) Model<F>(std::move(f)); inline_ = true;       // 小对象优化：不分配堆内存
    } else p_ = new Model<F>(std::move(f));
  }
  Function(const Function& o) { if (o.p_) { p_ = o.p_->clone(o.inline_ ? buf_ : nullptr); inline_ = o.inline_; } }
  Function(Function&& o) noexcept {
    if (!o.p_) return;
    if (o.inline_) { p_ = o.p_->move_to(buf_); inline_ = true; o.reset(); }
    else { p_ = std::exchange(o.p_, nullptr); }                      // 堆上的直接过户指针
  }
  Function& operator=(Function o) noexcept { reset(); if (o.p_) { if (o.inline_) { p_ = o.p_->move_to(buf_); inline_ = true; o.reset(); } else p_ = std::exchange(o.p_, nullptr), inline_ = false; } return *this; }
  ~Function() { reset(); }
  R operator()(A... a) { return p_->call(std::forward<A>(a)...); }
  explicit operator bool() const { return p_ != nullptr; }
  bool is_inline() const { return inline_; }
};

int add1(int x) { return x + 1; }
int main() {
  g_allocs = 0;
  int k = 10;
  Function<int(int)> f1 = [k](int x) { return x + k; };           // 捕获一个 int：很小
  std::printf("小 lambda：f1(5)=%d，内联存储=%d，堆分配 %d 次\n", f1(5), f1.is_inline(), g_allocs);
  std::string big(100, 'x');
  g_allocs = 0;
  Function<size_t(int)> f2 = [big](int x) { return big.size() + x; };  // 捕获 std::string(32 字节)：放不进缓冲区
  std::printf("大 lambda：f2(1)=%zu，内联存储=%d，堆分配 %d 次（lambda 捕获的 string 副本 + Model 对象）\n", f2(1), f2.is_inline(), g_allocs);
  Function<int(int)> f3 = add1;                                    // 函数指针
  Function<int(int)> f4 = f1;                                      // 拷贝：用 clone 复制具体类型
  Function<int(int)> f5 = std::move(f1);                           // 移动：内联对象要搬到新缓冲区
  Function<size_t(int)> f6 = std::move(f2);                        // 移动：堆上的对象只过户指针
  std::printf("函数指针 f3(1)=%d；拷贝 f4(5)=%d；移动后 f5(5)=%d，f6(1)=%zu，被移动的 f1 为空=%d\n", f3(1), f4(5), f5(5), f6(1), !f1);
}
```

运行结果（ASan + UBSan 下，没有报告）：

```text
小 lambda：f1(5)=15，内联存储=1，堆分配 0 次
大 lambda：f2(1)=101，内联存储=0，堆分配 2 次（lambda 捕获的 string 副本 + Model 对象）
函数指针 f3(1)=2；拷贝 f4(5)=15；移动后 f5(5)=15，f6(1)=101，被移动的 f1 为空=1
```

- 捕获一个 `int` 的 lambda：放在内联（inlining）缓冲区里，**0 次堆分配**。
- 捕获一个 `std::string`（32 字节）的 lambda：放不进 32 字节的缓冲区（还要加 vptr），走堆；2 次分配 = lambda 捕获的字符串副本（100 个字符，超过 SSO）+ `Model` 对象。
- 移动：内联对象要通过虚函数（virtual function） `move_to` 搬迁到新缓冲区（不能直接 `memcpy`，因为里面可能有自引用或非平凡类型）；堆上的对象只需要过户指针。这也是为什么我给内联存储要求 `is_nothrow_move_constructible_v<F>`：搬迁内联对象时不能让异常逃逸。
- 面试追问：**为什么要有 `clone`？** 因为 `Function` 要能拷贝，而具体类型在编译期（compile time）被擦除了，只能让具体类型自己来拷贝自己（虚函数）。**`std::function` 要求可调用对象可拷贝**，所以放不进只可移动的 lambda——C++23 的 `std::move_only_function` 解决了这个问题。

### 9.6 现代 C++ 面试题与答案要点

**Q97. `std::optional`、`std::variant`、`std::expected` 分别适合什么场景？**
见 9.1 与 7.6。

**Q98. `std::variant` 的 `valueless_by_exception` 是什么？**
当给 variant 赋新类型的值时，旧值先销毁，再构造新值；如果新值的构造抛异常，variant 就处于没有值的状态。用 `valueless_by_exception()` 检查；`std::visit` 对它会抛 `bad_variant_access`。设计上让备选类型的移动构造 `noexcept` 可以避免。

**Q99. 协程（coroutine）和线程有什么区别？协程的帧在哪里？**
见 9.2、9.3。协程是协作式、用户态的暂停恢复，共享栈外的堆帧；线程由内核调度、可并行。

**Q100. `string_view` 和 `span` 的使用风险？**
都是非拥有视图，悬空问题；`string_view` 不保证以 `\0` 结尾；`span` 不拥有元素；不要用 `string_view` 作为需要长期保存的成员，除非能保证源字符串存活。

**Q101. Ranges 视图为什么是惰性的，有什么陷阱？**
视图不存储结果，每次迭代时计算，所以组合便宜但多次遍历会重复计算；`views::filter` 需要缓存（cache）第一个满足条件的元素位置，所以在 const 上不能遍历；视图引用的底层范围必须活着；对右值（rvalue）容器应用视图适配器（adapter）会被拒绝（实验 18 的 `ranges::dangling`）。

**Q102. `<=>` 比较运算符？**
`operator<=>` 返回 `strong_ordering`/`weak_ordering`/`partial_ordering`，编译器据此合成 `<`、`<=`、`>`、`>=`；`= default` 按成员顺序逐个比较；`==` 需要单独声明（默认的 `<=>` 会同时隐式声明默认的 `==`）。

**Q103. 什么是 CTAD 与推导指引？**
从构造函数实参推导类模板参数：`std::vector v{1,2,3};`。推导指引在无法自动推导时手动指定：`template <class... Ts> overloaded(Ts...) -> overloaded<Ts...>;`（片段 D）。

**Q104. 讲讲 `std::visit` 与 overloaded 惯用法。**
片段 D：`struct overloaded : Ts... { using Ts::operator()...; };`，把若干 lambda 合并成一个重载集合，传给 `std::visit`。`visit` 对 variant 的所有备选类型编译期（compile time）生成跳转表，没有虚函数（virtual function）。

**Q105. C++20 模块（modules）相对头文件的优势和现状？**
优势：只解析一次、没有宏泄漏和包含顺序依赖、更快的编译。现状：构建系统与工具链支持逐步成熟，大型代码库迁移成本高，标准库的 `import std;` 在 C++23。（未验证具体编译器版本的支持程度。）

---

## 十、构建、链接与 ABI

### 10.1 为什么构建与链接是“高级”话题

“能写出来”和“能放进一个几百万行、多个团队、多个动态库（shared library）的生产系统”是两回事。线上最难查的问题常常发生在翻译单元（translation unit）的边界：初始化顺序、ODR、符号冲突、ABI 不兼容。

### 10.2 编译与链接模型

1. **预处理（preprocessing）**（`#include`、宏）→ 2. **编译**（每个 .cpp 即一个**翻译单元（translation unit）**，生成目标文件 .o）→ 3. **链接**（解析符号引用，合并目标文件和库，生成可执行文件/动态库（shared library））。
- **声明 vs 定义**；**单一定义规则（ODR）**：每个非内联（inlining）函数/变量在整个程序里只能有一个定义；内联函数、类、模板可以在多个翻译单元里有定义，但必须**完全相同**。
- **`inline` 的现代含义**：主要是“允许多个翻译单元里有相同定义”（头文件里的函数定义、C++17 的 `inline` 变量），不再是“请内联展开”；是否真的展开由优化器决定。
- **内部链接**：`static` 函数/变量、匿名命名空间（namespace）里的实体，只在本翻译单元可见，不参与 ODR 冲突。头文件里的 `const` 全局变量默认内部链接。
- **符号**：C++ 的函数名经过**名称修饰（name mangling）** 编码了命名空间、参数类型，所以能重载；`extern "C"` 关闭修饰，用于和 C 互操作和动态加载（`dlsym`）。`c++filt` 可以还原。
- **静态库（static library） vs 动态库**：静态库（.a）在链接时把用到的目标文件拷进可执行文件；动态库（.so）运行时加载，通过 PLT/GOT 间接调用，支持延迟绑定；符号默认全部导出，可以用 `-fvisibility=hidden` + 显式导出减小体积和启动时的符号解析开销，也避免意外的符号冲突和被替换。
- **LTO（链接时优化）**：把中间表示保留到链接阶段，跨翻译单元内联和去虚拟化（devirtualization）；编译慢、内存多。

### 10.3 静态初始化顺序问题（Static Initialization Order Fiasco）

同一个翻译单元（translation unit）里，全局/静态对象按定义顺序初始化；**不同翻译单元之间，动态初始化的先后顺序没有规定**（实际上通常取决于链接顺序）。如果 A 的全局对象的初始化依赖 B 里的全局对象，可能读到尚未初始化的值（先被零初始化，所以读到 0）。

### 10.4 实验 16：同一份代码，换个链接顺序，结果就变了

`a.cpp` 的全局变量 `a_copy = b_value + 1`，`b.cpp` 的 `b_value = compute()`（需要运行函数，所以是动态初始化）。

```cpp
// 实验 16：静态初始化顺序问题（static initialization order fiasco）。
// 不同翻译单元里的全局对象，动态初始化的先后顺序没有规定。这里 a.cpp 的全局变量在初始化时读取 b.cpp 的全局变量。
#include <cstdio>
extern int b_value;
int a_copy = b_value + 1;       // 动态初始化：依赖另一个翻译单元里的 b_value
int main() { std::printf("a_copy = %d（期望 b_value+1 = 101）\n", a_copy); }
```

```cpp
int compute() { return 100; }
int b_value = compute();       // 动态初始化（需要运行函数），不是常量初始化
```

运行结果：

```text
-- 链接顺序 a b --
a_copy = 1（期望 b_value+1 = 101）
-- 链接顺序 b a --
a_copy = 101（期望 b_value+1 = 101）
-- b 改为 constinit --
a_copy = 101（期望 b_value+1 = 101）
```

- 按 `a.cpp b.cpp` 的顺序链接，`a_copy` 先初始化，此时 `b_value` 还是零初始化的 0，所以 `a_copy = 1`。
- 按 `b.cpp a.cpp` 的顺序链接，`b_value` 先初始化，`a_copy = 101`。
- 把 `b_value` 改成 `constinit`（`constexpr compute()`），保证它在编译期（compile time）就完成**静态初始化**，不依赖顺序，两种顺序都正确。

**常用解决办法**：① `constinit`/`constexpr` 让初始化在编译期完成；② 函数内局部静态变量（“Meyers 单例”，首次使用时初始化，线程安全）；③ 避免全局对象之间的依赖；④ 注意**销毁顺序**同样有问题（`main` 返回后，全局对象按构造的逆序销毁，后台线程还在用它们就会崩溃）。

### 10.5 ABI（应用程序二进制接口）

- **ABI** 规定了二进制层面的约定：类型布局、名称修饰（name mangling）、调用约定、vtable 布局、异常处理等。API 兼容（源码能编译）不等于 ABI 兼容（旧的二进制能和新的库一起跑）。
- **libstdc++ 的双 ABI**：GCC 5 起因为 C++11 对 `std::string` 和 `std::list` 的要求改变，引入了 `_GLIBCXX_USE_CXX11_ABI` 宏（0 = 旧 ABI，1 = 新 ABI）。混用会出现链接错误（符号名里有 `__cxx11`），或者更糟，布局不一致导致崩溃。
- **保持库接口 ABI 稳定的做法**：C 接口 + 不透明指针；pimpl 惯用法（把成员藏在 .cpp 里的实现类，类大小不变）；不在接口里暴露标准库类型（`std::string` 的布局可能随标准库版本变）；不修改已发布的虚函数（virtual function）顺序；给导出符号加版本。
- **跨动态库（shared library）传递对象的风险**：在一个库里 `new`、另一个库里 `delete`（不同的堆/不同的 C 运行时，Windows 上尤其常见）；异常跨越边界；`std::string` 等跨库传递时使用不同的 ABI。

### 10.6 构建时间

- 头文件包含是主要原因：减少包含（前置声明、pimpl）、预编译头、unity build（把多个 .cpp 合并）、`ccache`/`sccache` 缓存（cache）、分布式编译（`distcc`、`icecc`）、模块（C++20）、减少模板膨胀（`extern template`）。
- 诊断：Clang 的 `-ftime-trace`，GCC 的 `-ftime-report`，`ninja -d stats`。

### 10.7 构建与链接面试题与答案要点

**Q106. 什么是 ODR？违反会怎样？**
见 10.2、Q77。链接器（linker）不检查，运行时表现为随机问题。

**Q107. 解释静态初始化顺序（static initialization order）问题及解决办法。**
见 10.3、实验 16。

**Q108. `inline` 关键字今天的作用？**
允许在多个翻译单元（translation unit）定义；是对编译器的建议（编译器可以忽略，也可以展开未标 inline 的函数）；C++17 的 `inline` 变量让头文件里能定义全局变量/静态成员。

**Q109. 名称修饰（name mangling）是什么？`extern "C"` 的作用？**
见 10.2。`extern "C"` 让函数使用 C 链接（无修饰），所以 C 代码可以调用，也能被 `dlsym` 按名字找到；它不能用于重载函数、成员函数、模板。

**Q110. 什么是 pimpl？优缺点？**
把实现细节放到 .cpp 里的私有结构体，类只持有一个指针（`unique_ptr<Impl>`）。优点：改实现不需要重新编译使用者、保持 ABI 稳定、减少头文件依赖；缺点：多一次间接寻址和一次堆分配、析构函数要在 .cpp 里定义（因为 `unique_ptr<Impl>` 需要完整类型）。

**Q111. 静态库（static library）和动态库（shared library）的区别？动态库的符号解析是怎样的？**
见 10.2。延迟绑定：第一次调用时通过 PLT 跳到动态链接器解析符号并写入 GOT；`LD_BIND_NOW` / `-z now` 让它启动时全部解析。符号插入（`LD_PRELOAD`）可以替换库函数，所以 `-fvisibility=hidden` 和 `-Bsymbolic` 有安全和性能意义。

**Q112. 为什么 `std::string` 在 GCC 里会出现 `_GLIBCXX_USE_CXX11_ABI` 相关的链接错误？**
见 10.5：预编译库和你的代码用了不同的 ABI 设置，符号名不同（`__cxx11` 命名空间（namespace）），链接时找不到。解决：统一用同一个设置重新编译，或使用和库匹配的设置。

**Q113. 编译很慢，你怎么优化？**
见 10.6：先测量（`-ftime-trace`），再针对性处理。

---

## 十一、陷阱代码题、手写题与工程场景

### 11.1 实验 17：十三个“看起来没问题”的代码陷阱

每一条都在真实编译器上运行过。先自己猜输出，再看结果。

```cpp
// 实验 17：面试里常见的“代码输出题”陷阱，每一条都在真实编译器上运行过，输出写在注释外面由程序打印。
#include <cstdio>
#include <initializer_list>
#include <map>
#include <string>
#include <typeinfo>
#include <vector>

// 1. 默认实参是静态绑定的，虚函数是动态绑定的
struct B1 { virtual void f(int x = 1) { std::printf("B1::f(%d)\n", x); } virtual ~B1() = default; };
struct D1 : B1 { void f(int x = 2) override { std::printf("D1::f(%d)\n", x); } };

// 2. 名字隐藏：派生类声明了同名函数，基类的所有重载都被隐藏
struct B2 { void g(int) { std::puts("B2::g(int)"); } void g(double) { std::puts("B2::g(double)"); } };
struct D2 : B2 { void g(const char*) { std::puts("D2::g(const char*)"); } };
struct D2b : B2 { using B2::g; void g(const char*) { std::puts("D2b::g(const char*)"); } };

// 3. 重载决议：字符串字面量更愿意变成 bool 而不是 std::string
void h(bool) { std::puts("h(bool)"); }
void h(const std::string&) { std::puts("h(const std::string&)"); }

// 4. 初始化列表构造函数优先
struct S { S(int, int) { std::puts("S(int,int)"); } S(std::initializer_list<int>) { std::puts("S(initializer_list)"); } };

// 5. 切片
struct Animal { virtual const char* name() const { return "Animal"; } virtual ~Animal() = default; };
struct Cat : Animal { const char* name() const override { return "Cat"; } };
void by_value(Animal a) { std::printf("按值传递：%s\n", a.name()); }
void by_ref(const Animal& a) { std::printf("按引用传递：%s\n", a.name()); }

// 6. 构造函数中的虚调用 / 7. 静态局部变量只初始化一次
int next_id() { static int id = 100; return ++id; }

// 8. 析构顺序
struct Noisy { const char* n; explicit Noisy(const char* n) : n(n) { std::printf("构造 %s\n", n); } ~Noisy() { std::printf("析构 %s\n", n); } };
struct Holder { Noisy a{"成员a"}; Noisy b{"成员b"}; Holder() { std::puts("Holder 构造体"); } ~Holder() { std::puts("Holder 析构体"); } };

int main() {
  std::puts("--1 默认实参静态绑定--");  { B1* p = new D1; p->f(); delete p; }
  std::puts("--2 名字隐藏--");  { D2 d; d.g("x"); /* d.g(1) 在这里无法通过编译：g++ 报 invalid conversion from int to const char*，因为 B2::g 被隐藏了 */ }
  std::puts("--2b using 声明恢复重载--");  { D2b d; d.g(1); d.g(1.5); d.g("x"); }
  std::puts("--3 字符串字面量重载--");  h("hello"); h(std::string("hello"));
  std::puts("--4 花括号与圆括号--");  { S a(1, 2); S b{1, 2}; S c = {1, 2}; (void)a; (void)b; (void)c; }
  { std::vector<int> v1(3, 4), v2{3, 4}; std::printf("vector<int> v1(3,4) 大小 %zu；v2{3,4} 大小 %zu\n", v1.size(), v2.size()); }
  std::puts("--5 切片--");  { Cat c; by_value(c); by_ref(c); }
  std::puts("--6 有符号与无符号比较--");
  { int a = -1; unsigned b = 1; std::printf("-1 < 1u 的结果：%d（-1 被转成很大的无符号数）\n", a < b); }
  { std::vector<int> v; std::printf("v.size() - 1 = %zu （空 vector 上的无符号下溢）\n", v.size() - 1); }
  std::puts("--7 auto 与花括号--");
  { auto a = {1}; auto b = 1; std::printf("auto a = {1}: %s；auto b = 1: %s\n", typeid(a).name(), typeid(b).name()); }
  std::puts("--8 map::operator[] 会插入--");
  { std::map<std::string, int> m; if (m["missing"] == 0) {} std::printf("只是读了一下，map 大小变成 %zu\n", m.size()); }
  std::puts("--9 静态局部变量只初始化一次；同一个调用里多个实参的求值顺序未指定--");  std::printf("%d %d %d\n", next_id(), next_id(), next_id());   // GCC 通常从右往左求值，Clang 从左往右
  std::puts("--10 成员的构造与析构顺序--");  { Holder h; }
  std::puts("--11 数组退化--");
  { int arr[10]; auto f = [](int a[10]) { return sizeof(a); }; std::printf("sizeof(arr)=%zu；传给 int a[10] 参数后 sizeof(a)=%zu\n", sizeof(arr), f(arr)); }
  std::puts("--12 vector<bool> 不是容器--");
  { std::vector<bool> vb{true}; auto x = vb[0]; vb[0] = false; std::printf("auto x = vb[0]; 然后 vb[0]=false；x 现在是 %d（x 是代理对象，仍然引用着 vector 里的那一位）\n", (bool)x); }
  std::puts("--13 临时对象的生命周期--");
  { const std::string& r = std::string("临时对象被延长生命周期"); std::printf("%s\n", r.c_str()); }
}
```

运行结果：

```text
--1 默认实参静态绑定--
D1::f(1)
--2 名字隐藏--
D2::g(const char*)
--2b using 声明恢复重载--
B2::g(int)
B2::g(double)
D2b::g(const char*)
--3 字符串字面量重载--
h(bool)
h(const std::string&)
--4 花括号与圆括号--
S(int,int)
S(initializer_list)
S(initializer_list)
vector<int> v1(3,4) 大小 3；v2{3,4} 大小 2
--5 切片--
按值传递：Animal
按引用传递：Cat
--6 有符号与无符号比较--
-1 < 1u 的结果：0（-1 被转成很大的无符号数）
v.size() - 1 = 18446744073709551615 （空 vector 上的无符号下溢）
--7 auto 与花括号--
auto a = {1}: St16initializer_listIiE；auto b = 1: i
--8 map::operator[] 会插入--
只是读了一下，map 大小变成 1
--9 静态局部变量只初始化一次；同一个调用里多个实参的求值顺序未指定--
103 102 101
--10 成员的构造与析构顺序--
构造 成员a
构造 成员b
Holder 构造体
Holder 析构体
析构 成员b
析构 成员a
--11 数组退化--
sizeof(arr)=40；传给 int a[10] 参数后 sizeof(a)=8
--12 vector<bool> 不是容器--
auto x = vb[0]; 然后 vb[0]=false；x 现在是 0（x 是代理对象，仍然引用着 vector 里的那一位）
--13 临时对象的生命周期--
临时对象被延长生命周期
-- 同一个程序用 clang++ 编译，第 9 项 --
--9 静态局部变量只初始化一次；同一个调用里多个实参的求值顺序未指定--
101 102 103
```

逐条解释：

1. **默认实参是静态绑定的**：`B1* p = new D1; p->f();` 调用的是 `D1::f`（虚函数（virtual function）动态绑定），但默认实参 `x` 取的是 `B1::f` 声明里的 `1`，所以打印 `D1::f(1)`。**不要在虚函数里改默认实参。**
2. **名字隐藏**：`D2` 声明了 `g(const char*)`，基类的 `g(int)`、`g(double)` 全部被隐藏；`d.g(1)` 无法编译（g++ 报 `invalid conversion from int to const char*`）。`using B2::g;` 把基类的重载重新引入。
3. **字符串字面量更愿意变成 `bool`**：`h("hello")` 调用的是 `h(bool)`（标准转换，指针到 bool），而不是需要用户定义转换的 `h(const std::string&)`。
4. **花括号初始化偏爱 `initializer_list` 构造函数**：`S b{1,2}` 和 `S c = {1,2}` 调用 `initializer_list` 版本；`vector<int> v1(3,4)` 是 3 个 4，`v2{3,4}` 是两个元素 3、4。
5. **切片**：按值传递丢掉了派生类部分。
6. **有符号/无符号比较**：`-1 < 1u` 是 false，`v.size() - 1` 在空 vector 上是 18446744073709551615。编译器会警告 `-Wsign-compare`。
7. **`auto a = {1}`** 推导为 `std::initializer_list<int>`（`typeid` 名字 `St16initializer_listIiE`），`auto b = 1` 是 `int`。
8. **`map::operator[]` 会插入**：仅仅是“读”一下不存在的键，map 大小变成 1。用 `find`、`contains` 或 `at`。
9. **同一调用中多个实参的求值顺序未指定**：g++ 打印 `103 102 101`（右到左），clang++ 打印 `101 102 103`。
10. **成员按声明顺序构造、按相反顺序析构**；构造函数体在所有成员构造之后、析构函数体在成员析构之前运行。
11. **数组形参会退化为指针**：`int a[10]` 作为函数参数时 `sizeof(a)` 是 8（指针大小），编译器警告 `-Wsizeof-array-argument`。
12. **`vector<bool>` 的 `operator[]` 返回代理对象**：`auto x = vb[0]` 得到的是代理，不是 `bool`，它仍然引用着容器里的那一位；之后修改容器，`x` 的值随之变化。因此 `vector<bool>` 不满足容器要求，不能取元素的地址；需要真正的 `bool` 数组时用 `std::vector<char>` 或 `std::deque<bool>`、`std::bitset`。
13. **绑定到 `const` 引用的临时对象，生命周期被延长到引用的作用域**（但绑定到函数返回的引用时不适用）。

### 11.2 手写题清单（以及它们考什么）

| 题目 | 考点 | 本材料里的实现 |
|---|---|---|
| `unique_ptr` | 移动语义（move semantics）、删除器（deleter）、`explicit`、`release/reset/swap` | 第二章的原则可直接用 |
| `shared_ptr` + `weak_ptr` | 控制块（control block）、原子计数、`lock()` 的 CAS | 实验 5 |
| `std::function` | 类型擦除（type erasure）、SBO、拷贝/移动 | 实验 15 |
| 线程池（thread pool） | 条件变量（condition variable）、`future`、关闭流程 | 实验 9 |
| SPSC 无锁（lock-free）队列 | 内存序（memory order）、伪共享（false sharing）、缓存行（cache line） | 实验 7 |
| `vector` | 动态数组、`reserve`、强异常保证、`move_if_noexcept` | 实验 2、11 |
| 内存池（memory pool） / 竞技场（arena）分配器（allocator） | 对齐（alignment）、空闲链表、`pmr` | 4.3 |
| LRU 缓存（cache） | 哈希表 + 双向链表，O(1) | 与语言无关，看数据结构选择 |
| `std::string` | SSO、拷贝/移动、`c_str()` 以 `\0` 结尾 | 实验 12 |
| RAII `scope_guard` | 析构函数、`std::function` 或模板、`noexcept` | 第七章 |
| 单例、观察者（用 `weak_ptr`） | 线程安全初始化、生命周期 | 5.2、4.4 |
| 有序的订单簿（HFT） | 价位层数据结构（连续数组 vs map）、缓存友好、无分配 | 8.6 的原则 |

写手写题的方法：先声明接口和不变式；先写出最简单正确的版本，再说明可以怎样优化；主动说明你**没有**处理的边界（构造时 `new` 失败、自赋值、异常安全（exception safety）、多线程）。

### 11.3 线上故障场景题

**场景：C++ 服务在生产环境崩溃，或内存持续增长。你怎么处理？**

1. **止血**：回滚到上一个稳定版本、限流/摘流量、重启并保留现场（core dump）。
2. **取证**：
   - 崩溃：确认开启了 core dump（`ulimit -c`、`/proc/sys/kernel/core_pattern`），用带符号的二进制（保留调试符号或单独的 `.debug` 文件）打开：`gdb ./binary core`，`bt`、`thread apply all bt`、`info registers`；看崩溃地址（0 附近是空指针；很大的奇怪值常是野指针或栈破坏）。
   - 内存增长：先分清是泄漏、碎片还是缓存（cache）/容器无限增长；`pmap`、`/proc/<pid>/smaps`；jemalloc/tcmalloc 的堆剖析；heaptrack；`valgrind --leak-check`（预发布环境）；`LD_PRELOAD` 方式的 `libasan`/`LeakSanitizer`。
   - CPU 高：`perf top`/`perf record -g` 与火焰图（flame graph）；看是不是自旋锁、频繁分配、日志、序列化。
3. **复现**：在预发布环境用 ASan+UBSan 构建重放流量；TSan 查数据竞争（data race）；`rr` 记录重放；缩小输入（delta debugging）。
4. **根因分析**：常见：释放后使用、迭代器失效（iterator invalidation）、数据竞争、栈溢出（stack overflow）、未初始化变量、整数溢出、ODR 违反、不同库版本 ABI 不匹配。
5. **防再发**：加测试和断言、CI 里长期运行 sanitizer、模糊测试、代码评审清单、监控（RSS、fd、线程数）、金丝雀发布。

**场景：线程数增加，吞吐反而下降。** 排查：锁竞争（`perf` 看 `futex`、`pthread_mutex_lock`）、伪共享（false sharing，`perf c2c`）、共享的原子计数器热点、内存分配器（allocator）竞争（换 tcmalloc/jemalloc 或线程本地缓存）、NUMA 跨节点访问、过度的上下文切换。

**场景：延迟尾部（p99）很高。** 排查：GC 无（C++ 没有），但有：堆分配抖动、缺页（预热）、锁等待、系统调用、日志同步写盘、CPU 频率/节能状态、中断、定时器；绑核、实时优先级、关闭透明大页的后台整理。

---

## 十二、把知识串起来：自测表

| 主题 | 你应该能讲清 |
|---|---|
| 对象模型（object model） | 填充（padding）与重排、EBO、vptr/vtable、多重继承（multiple inheritance）的指针偏移、构造期间的动态类型 |
| 值类别（value category）与移动 | 五种值类别、`std::move` 只是转换、转发引用（forwarding reference）与引用折叠（reference collapsing）、`return std::move` 的问题、`noexcept` 移动与 vector 扩容 |
| 模板 | 两阶段查找（two-phase lookup）、SFINAE 与 Concepts、`if constexpr`、CRTP、类型推导（type deduction）规则、`constinit` |
| 内存与所有权 | new 表达式 vs operator new、placement new、pmr、`shared_ptr` 控制块（control block）与线程安全、`make_shared` 取舍、循环引用（circular reference） |
| 并发（concurrency） | 数据竞争（data race）、happens-before、acquire/release 与 seq_cst、ABA、条件变量（condition variable）谓词、伪共享（false sharing）、SPSC 队列 |
| 未定义行为 | 常见 UB 清单、编译器如何利用 UB、严格别名（strict aliasing）、sanitizer 组合 |
| 异常 | 零开销模型的含义、四级异常安全（exception safety）、`noexcept`、copy-and-swap、析构函数不抛 |
| STL 与性能 | 迭代器失效（iterator invalidation）、SSO、unordered_map 实现、缓存局部性（cache locality）、分支预测（branch prediction）、内联（inlining）的价值、微基准（microbenchmark）陷阱 |
| 现代 C++ | 协程（coroutine）的帧与 promise、类型擦除（type erasure）、variant/optional/expected、ranges 悬空（dangling）、`<=>` |
| 构建与 ABI | ODR、静态初始化顺序（static initialization order）、名称修饰（name mangling）、双 ABI、pimpl、LTO |
| 工程 | core dump 分析流程、ASan/TSan 在 CI 中的使用、性能剖析方法 |

---

## 附录 A：来源与说明

**我搜到并参考了主题范围的页面**（都是二手备考内容，没有日期，没有可核实的具体公司面经；只用来确认常考主题）：

- 通用题库：[Hyring：Top 60 C++ Interview Questions (2026)](https://hyring.com/jobseeker-toolkit/interview-questions/technical/cpp)、[TechPrep：128 C++ Interview Questions and Answers](https://www.techprep.app/blog/cpp-interview-questions)、[Hire in South：Top C++ Interview Questions to Ask in 2026](https://www.hireinsouth.com/post/c-plus-plus-interview-questions)、[CodeSignal：从初级到高级的 C++ 练习题](https://codesignal.com/blog/interview-prep/key-cpp-practice-problems-and-solutions-from-beginner-to-senior-level/)
- 高频交易与低延迟方向：[techinterview.org：C++ for Quants](https://www.techinterview.org/post/3233474597/cpp-quant-interviews/)、[techinterview.org：HFT 面试里反复出现的无锁队列题](https://www.techinterview.org/post/3233476386/lock-free-queue-hft-interview-question/)、[quantvault：低延迟 C++ 面试题](https://quantvault.org/cpp-low-latency-interview-questions.html)、[quantt：C++ 量化面试题](https://www.quantt.co.uk/resources/cpp-quant-interview-questions)
- 权威来源应以 ISO C++ 标准、cppreference.com、编译器文档（GCC、Clang）和 Itanium C++ ABI 文档为准。

**已验证（真实编译并运行）**：全部 18 个实验，用 g++ 13.3.0 和 clang++ 18.1.3，x86-64 Linux（4 核）；并发（concurrency）代码用 ThreadSanitizer 检查，内存相关代码用 AddressSanitizer / UndefinedBehaviorSanitizer 检查。实验源码与样例输出在 `cpp-advanced/code/` 和 `cpp-advanced/sample_output/`。

**依赖实现的结果（换编译器/标准库/平台会不同）**：对象布局与 vptr（Itanium ABI）、`std::string` 的 SSO 容量、vector 的扩容倍数、unordered_map 的桶序列、实参求值顺序、性能数字、伪共享（false sharing）与存储缓冲（store buffer）的重排频率（取决于 CPU）。

**我没有验证的内容**：
- C++26 的所有特性（静态反射、契约、`std::execution`、hazard pointer/RCU、`std::function_ref` 等），我只写了方向，未对照最终标准。
- 编译器对 C++20/23 特性（模块（modules）、`std::print`、`std::flat_map` 等）在你所用版本上的支持。
- 其他平台（MSVC、ARM、macOS）上的行为：我只提到了差异，没有实测；弱内存序（memory order）平台上错误内存序的实际表现我没有测。
- 我提到的一些库与工具的具体行为（jemalloc/tcmalloc 的统计接口、`perf c2c`、`-Wodr`）来自我的知识，没有在这个环境里运行。
- 增长因子与黄金比例的说法、各项开销的一般数量级（缓存（cache）延迟等）是常见说法，非本实验测得。
- **这份材料里没有真实的、带日期的某公司 C++ 面经。**

## 附录 B：术语表（中英对照）

按在文中第一次出现的顺序排列。

- 虚函数：virtual function
- 控制块：control block
- 未定义行为：UB, undefined behavior
- 无锁：lock-free
- 线程池：thread pool
- 内存池：memory pool
- 缓存：cache
- 分支预测：branch prediction
- 伪共享：false sharing
- 内联：inlining
- 内存模型：memory model
- 并发：concurrency
- 智能指针：smart pointer
- 分配器：allocator
- 数据导向设计：data-oriented design
- 多重继承：multiple inheritance
- 多态：polymorphism
- 填充：padding
- 缓存行：cache line
- 对齐：alignment
- 删除器：deleter
- 虚继承：virtual inheritance
- 标准布局：standard-layout
- 平凡可拷贝：trivially copyable
- 位域：bit-field
- 数据竞争：data race
- 联合体：union
- 类型双关：type punning
- 去虚拟化：devirtualization
- 移动语义：move semantics
- 值类别：value category
- 转发引用：forwarding reference
- 右值：rvalue
- 左值：lvalue
- 引用折叠：reference collapsing
- 拷贝省略：copy elision
- 纯右值：prvalue
- 三法则：rule of three
- 五法则：rule of five
- 零法则：rule of zero
- 异常安全：exception safety
- 完美转发：perfect forwarding
- 悬空：dangling
- 编译期：compile time
- 代码膨胀：code bloat
- 两阶段查找：two-phase lookup
- 实例化：instantiation
- 参数依赖查找：ADL, argument-dependent lookup
- 翻译单元：translation unit
- 链接器：linker
- 偏特化：partial specialization
- 特化：specialization
- 运行期：run time
- 折叠表达式：fold expression
- 静态多态：static polymorphism
- 类型擦除：type erasure
- 静态初始化顺序：static initialization order
- 模块：modules
- 悬空指针：dangling pointer
- 对象池：object pool
- 空基类优化：EBO, empty base optimization
- 引用计数：reference counting
- 循环引用：circular reference
- 原子操作：atomic operation
- 内存序：memory order
- 内存泄漏：memory leak
- 栈溢出：stack overflow
- 重排序：reordering
- 死锁：deadlock
- 条件变量：condition variable
- 虚假唤醒：spurious wakeup
- 存储缓冲：store buffer
- 竞态条件：race condition
- 严格别名：strict aliasing
- 未指定行为：unspecified behavior
- 实现定义行为：implementation-defined behavior
- 迭代器失效：iterator invalidation
- 命名空间：namespace
- 栈展开：stack unwinding
- 动态库：shared library
- 小字符串优化：SSO, small string optimization
- 缓存局部性：cache locality
- 微基准：microbenchmark
- 火焰图：flame graph
- 协程：coroutine
- 协程帧：coroutine frame
- 适配器：adapter
- 预处理：preprocessing
- 单一定义规则：ODR, one definition rule
- 名称修饰：name mangling
- 静态库：static library
- 竞技场：arena
- 对象模型：object model
- 类型推导：type deduction
