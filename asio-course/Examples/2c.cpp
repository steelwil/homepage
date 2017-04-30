#include <iostream>
#include <functional>

void F2(int i, float f)
{
    std::cout << "i: " << i << std::endl;
    std::cout << "f: " << f << std::endl;
}

int main(int argc, char * argv[])
{
    std::bind(&F2, 42, 3.14f)();
    return 0;
}
