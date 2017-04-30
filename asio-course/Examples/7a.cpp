#include <asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <iostream>
#include <string>

std::mutex global_stream_lock;

void WorkerThread(std::shared_ptr<asio::io_service> io_service)
{
    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id() << "] Thread Start" << std::endl;
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
                std::cout << "[" << std::this_thread::get_id() << "] Error: " << ec << std::endl;
                global_stream_lock.unlock();
            }

            break;
        }
        catch (std::exception& ex)
        {
            global_stream_lock.lock();
            std::cout << "[" << std::this_thread::get_id() << "] Exception: " << ex.what() << std::endl;
            global_stream_lock.unlock();
        }
    }

    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id() << "] Thread Finish" << std::endl;
    global_stream_lock.unlock();
}

int main(int argc, char* argv[])
{
    std::shared_ptr<asio::io_service> io_service(new asio::io_service);
    std::shared_ptr<asio::io_service::work> work(new asio::io_service::work(*io_service));
    std::shared_ptr<asio::io_service::strand> strand(new asio::io_service::strand(*io_service));

    global_stream_lock.lock();
    std::cout << "[" << std::this_thread::get_id() << "] Press [return] to exit." << std::endl;
    global_stream_lock.unlock();

    std::thread worker_threads[2];

    for (int x = 0; x < 2; ++x)
    {
        worker_threads[x] = std::thread(std::bind(&WorkerThread, io_service));
    }

    asio::ip::tcp::socket sock(*io_service);

    try
    {
        asio::ip::tcp::resolver resolver(*io_service);
        asio::ip::tcp::resolver::query query("www.google.com", std::to_string(80));
        asio::ip::tcp::resolver::iterator iterator = resolver.resolve(query);
        asio::ip::tcp::endpoint endpoint = *iterator;

        global_stream_lock.lock();
        std::cout << "Connecting to: " << endpoint << std::endl;
        global_stream_lock.unlock();

        sock.connect(endpoint);
    }
    catch (std::exception& ex)
    {
        global_stream_lock.lock();
        std::cout << "[" << std::this_thread::get_id() << "] Exception: " << ex.what() << std::endl;
        global_stream_lock.unlock();
    }

    std::cin.get();

    asio::error_code ec;
    sock.shutdown(asio::ip::tcp::socket::shutdown_both, ec);
    sock.close(ec);

    io_service->stop();

    for (int x = 0; x < 2; ++x)
    {
        worker_threads[x].join();
    }

    return 0;
}
