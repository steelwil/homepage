#include <asio.hpp>
#include <memory>
#include <thread>
#include <iostream>

asio::io_service io_service;

void WorkerThread()
{
    std::cout << "Thread Start\n";
    io_service.run();
    std::cout << "Thread Finish\n";
}

int main(int argc, char * argv[])
{
    std::shared_ptr< asio::io_service::work > work(
        new asio::io_service::work(io_service)
    );

    std::cout << "Press [return] to exit." << std::endl;

    std::thread worker_threads[4];

    for (int x = 0; x < 4; ++x)
    {
        worker_threads[x] = std::thread(WorkerThread);
    }

    std::cin.get();

    io_service.stop();

    for (int x = 0; x < 4; ++x)
    {
        worker_threads[x].join();
    }

    return 0;
}
