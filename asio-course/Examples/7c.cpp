#include <asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <iostream>
#include <string>

using namespace std::placeholders; // adds _1, _2, ...
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

void OnAccept(const asio::error_code& ec, std::shared_ptr<asio::ip::tcp::socket> sock)
{
    if (ec)
    {
        global_stream_lock.lock();
        std::cout << "[" << std::this_thread::get_id() << "] Error: " << ec << std::endl;
        global_stream_lock.unlock();
    }
    else
    {
        global_stream_lock.lock();
        std::cout << "[" << std::this_thread::get_id() << "] Accepted!" << std::endl;
        global_stream_lock.unlock();
    }
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

    std::shared_ptr<asio::ip::tcp::acceptor> acceptor(new asio::ip::tcp::acceptor(*io_service));
    std::shared_ptr<asio::ip::tcp::socket> sock(new asio::ip::tcp::socket(*io_service));

    try
    {
        asio::ip::tcp::resolver resolver(*io_service);
        asio::ip::tcp::resolver::query query("127.0.0.1", std::to_string(7777));
        asio::ip::tcp::endpoint endpoint = *resolver.resolve(query);
        acceptor->open(endpoint.protocol());
        acceptor->set_option(asio::ip::tcp::acceptor::reuse_address(false));
        acceptor->bind(endpoint);
        acceptor->listen(asio::socket_base::max_connections);
        acceptor->async_accept(*sock, std::bind(OnAccept, _1, sock));

        global_stream_lock.lock();
        std::cout << "Listening on: " << endpoint << std::endl;
        global_stream_lock.unlock();
    }
    catch (std::exception& ex)
    {
        global_stream_lock.lock();
        std::cout << "[" << std::this_thread::get_id() << "] Exception: " << ex.what() << std::endl;
        global_stream_lock.unlock();
    }

    std::cin.get();

    asio::error_code ec;
    acceptor->close(ec);

    sock->shutdown(asio::ip::tcp::socket::shutdown_both, ec);
    sock->close(ec);

    io_service->stop();

    for (int x = 0; x < 2; ++x)
    {
        worker_threads[x].join();
    }

    return 0;
}
