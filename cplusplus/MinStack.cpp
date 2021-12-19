#include <stack>

class MinStack {
public:
    MinStack() {
    }
    
    void push(int val) {
        this->store.push(val);
        if (min.empty() || val <= min.top()) {
            min.push(val);
        }
    }
    
    void pop() {
        if (store.top() == min.top()) {
            min.pop();
        }
        store.pop();
    }
    
    int top() {
        return store.top();    
    }
    
    int getMin() {
        return min.top(); 
    }

private:
    std::stack<int> store;
    std::stack<int> min;
};

/**
 * Your MinStack object will be instantiated and called as such:
 * MinStack* obj = new MinStack();
 * obj->push(val);
 * obj->pop();
 * int param_3 = obj->top();
 * int param_4 = obj->getMin();
 */