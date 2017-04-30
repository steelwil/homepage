#include <iostream>
#include <functional>

class MyClass
{
public:
    void F3(int i, float f)
    {
        std::cout << "i: " << i << std::endl;
        std::cout << "f: " << f << std::endl;
    }
};

int main(int argc, char * argv[])
{
    MyClass c;
    std::bind(&MyClass::F3, &c, 42, 3.14f)();
    return 0;
}
