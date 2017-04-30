#include <asio.hpp>
#include <memory>
#include <iostream>

int main(int argc, char * argv[])
{
    asio::io_service io_service;
    std::shared_ptr< asio::io_service::work > work(
        new asio::io_service::work(io_service)
    );

    work.reset();

    io_service.run();

    std::cout << "Do you reckon this line displays?" << std::endl;

    return 0;
}
