#include <bits/stdc++.h>

using namespace std;

int main() {
    mt19937 rnd(random_device{}());
    string alph = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    uniform_int_distribution<int> dist(0, alph.size());
    while (1) {
        for (int i = 0; i < 100; ++i) {
            cout << alph[dist(rnd)];
        }
        cout << '\n' << flush;
    }
    return 0;
}
