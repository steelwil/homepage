#include <asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <iostream>
#include <chrono>

std::mutex global_stream_lock;

void WorkerThread(std::shared_ptr< asio::io_service > io_service)
{
    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id()
              << "] Thread Start" << std::endl;
    global_stream_lock.unlock();

    io_service->run();

    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id()
              << "] Thread Finish" << std::endl;
    global_stream_lock.unlock();
}

void Dispatch(int x)
{
    global_stream_lock.lock();
    std::cout << "[" <<  std::this_thread::get_id()  << "] "
              << __FUNCTION__  << " x = " << x <<  std::endl;
    global_stream_lock.unlock();
}

void Post(int x)
{
    global_stream_lock.lock();
    std::cout << "[" <<  std::this_thread::get_id()  << "] "
              << __FUNCTION__  << " x = " << x <<  std::endl;
    global_stream_lock.unlock();
}

void Run3(std::shared_ptr< asio::io_service > io_service)
{
    for (int x = 0; x < 3; ++x)
    {
        io_service->dispatch(std::bind(&Dispatch, x * 2));
        io_service->post(std::bind(&Post, x * 2 + 1));
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    }
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
    std::cout << "[" <<  std::this_thread::get_id()
              << "] The program will exit when all  work has finished." <<  std::endl;
    global_stream_lock.unlock();

    std::thread worker_threads[4];

    for (int x = 0; x < 1; ++x)
    {
        worker_threads[x] = std::thread(std::bind(&WorkerThread, io_service));
    }

    io_service->post(std::bind(&Run3, io_service));

    work.reset();

    for (int x = 0; x < 1; ++x)
    {
        worker_threads[x].join();
    }

    return 0;
}
