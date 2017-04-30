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
    std::cout << "[" << std::this_thread::get_id()
              << "] Thread Start" << std::endl;
    global_stream_lock.unlock();

    try
    {
        io_service->run();
    }
    catch (std::exception & ex)
    {
        global_stream_lock.lock();
        std::cout << "[" << std::this_thread::get_id()
                  << "] Exception: " << ex.what() << std::endl;
        global_stream_lock.unlock();
    }

    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id()
              << "] Thread Finish" << std::endl;
    global_stream_lock.unlock();
}

void RaiseAnException(std::shared_ptr< asio::io_service > io_service)
{
    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id()
              << "] " << __FUNCTION__ << std::endl;
    global_stream_lock.unlock();

    io_service->post(std::bind(&RaiseAnException, io_service));

    throw (std::runtime_error("Oops!"));
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
              << "] The program will exit when all work has finished." << std::endl;
    global_stream_lock.unlock();

    std::thread worker_threads[2];

    for (int x = 0; x < 2; ++x)
    {
        worker_threads[x] = std::thread(std::bind(&WorkerThread, io_service));
    }

    io_service->post(std::bind(&RaiseAnException, io_service));

    for (int x = 0; x < 2; ++x)
    {
        worker_threads[x].join();
    }

    return 0;
}
