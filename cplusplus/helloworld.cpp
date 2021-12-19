#include <vector>
#include <string>
#include <iostream>

using namespace std;

int main() {
    vector<string> msg{"Hello", "C++"};

    for (const string& word : msg)
    {
        cout << word << " ";
    }
    cout << endl;

    return 0;
}