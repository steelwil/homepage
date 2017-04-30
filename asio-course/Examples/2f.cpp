#include <asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <iostream>

std::mutex global_stream_lock;

void WorkerThread(std::shared_ptr< asio::io_service > io_service)
{
    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id() <<
              "] Thread Start" << std::endl;
    global_stream_lock.unlock();

    io_service->run();

    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id() <<
              "] Thread Finish" << std::endl;
    global_stream_lock.unlock();
}

int main(int argc, char * argv[])
{
    std::shared_ptr< asio::io_service > io_service(
        new asio::io_service
    );
    std::shared_ptr< asio::io_service::work > work(
        new asio::io_service::work(*io_service)
    );

    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id()
              << "] Press [return] to exit." << std::endl;
    global_stream_lock.unlock();

    std::thread worker_threads[4];

    for (int x = 0; x < 4; ++x)
    {
        worker_threads[x] = std::thread(std::bind(&WorkerThread, io_service));
    }

    std::cin.get();

    io_service->stop();

    for (int x = 0; x < 4; ++x)
    {
        worker_threads[x].join();
    }

    return 0;
}
