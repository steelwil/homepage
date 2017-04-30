#include <asio.hpp>
#include <iostream>

int main(int argc, char * argv[])
{
    asio::io_service io_service;
    asio::io_service::work work(io_service);

    io_service.run();

    std::cout << "Do you reckon this line displays?" << std::endl;

    return 0;
}