#define ASIO_STANDALONE

#include <asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <iostream>

using namespace std::placeholders; // adds _1, _2, ...
std::mutex global_stream_lock;

void WorkerThread(std::shared_ptr< asio::io_service > io_service)
{
    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id()
              << "] Thread Start" << std::endl;
    global_stream_lock.unlock();

    while (true)
    {
        try
        {
            asio::error_code ec;
            io_service->run(ec);

            if (ec)
            {
                global_stream_lock.lock();
                std::cout << "[" << std::this_thread::get_id()
                          << "] Error: " << ec << std::endl;
                global_stream_lock.unlock();
            }

            break;
        }
        catch (std::exception & ex)
        {
            global_stream_lock.lock();
            std::cout << "[" << std::this_thread::get_id()
                      << "] Exception: " << ex.what() << std::endl;
            global_stream_lock.unlock();
        }
    }

    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id()
              << "] Thread Finish" << std::endl;
    global_stream_lock.unlock();
}

void TimerHandler(
    const asio::error_code & error,
    std::shared_ptr< asio::steady_timer > timer
)
{
    if (error)
    {
        global_stream_lock.lock();
        std::cout << "[" << std::this_thread::get_id()
                  << "] Error: " << error << std::endl;
        global_stream_lock.unlock();
    }
    else
    {
        global_stream_lock.lock();
        std::cout << "[" << std::this_thread::get_id()
                  << "] TimerHandler " << std::endl;
        global_stream_lock.unlock();

        timer->expires_from_now(std::chrono::seconds(5));
        timer->async_wait(std::bind(&TimerHandler, _1, timer));
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
    std::cout << "[" << std::this_thread::get_id()
              << "] Press [return] to exit." << std::endl;
    global_stream_lock.unlock();

    std::thread worker_threads[2];

    for (int x = 0; x < 2; ++x)
    {
        worker_threads[x] = std::thread(std::bind(&WorkerThread, io_service));
    }

    std::shared_ptr< asio::steady_timer > timer(
        new asio::steady_timer(*io_service)
    );
    timer->expires_from_now(std::chrono::seconds(5));
    timer->async_wait(std::bind(&TimerHandler, _1, timer));

    std::cin.get();

    io_service->stop();

    for (int x = 0; x < 2; ++x)
    {
        worker_threads[x].join();
    }

    return 0;
}
