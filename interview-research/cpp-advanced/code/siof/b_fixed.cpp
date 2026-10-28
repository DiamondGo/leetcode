constexpr int compute() { return 100; }
constinit int b_value = compute();   // constinit：保证编译期常量初始化，不依赖顺序
