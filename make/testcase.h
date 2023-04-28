#include <bits/stdc++.h>

void testcase(const std::string& name, const std::string& description, const std::string& input) {
  std::ofstream desc_file(name + ".desc"), in_file(name + ".in");
  desc_file << description;
  in_file << input;
  if (input.back() != '\n')
    in_file << '\n';
}

void order_testcase(const std::string& description, const std::string& input) {
  static int id = 0;
  std::string name = "_" + toString(id++);
  for (long long x = ssize(input), i = 6; i; x /= 26, i--)
    name = char('a' + (x % 26)) + name;
  testcase(name, description, input);
}

void sample(const std::string& content) {
  static int idx = 1;
  auto idx_str = toString(idx++);
  testcase("sample" + idx_str, "Sample #" + idx_str, content);
}
