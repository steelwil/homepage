#include <iostream>
#include <functional>

void F1()
{
    std::cout << __FUNCTION__ << std::endl;
}

int main(int argc, char * argv[])
{
    std::bind(&F1)();
    return 0;
}
