#include "network.h"
#include <iostream>
#include <iomanip>
#include <mutex>
#include <thread>

std::mutex global_stream_lock;

class MyConnection : public Connection
{
private:
    void OnAccept(const std::string& host, uint16_t port)
    {
        global_stream_lock.lock();
        std::cout << "[" << __FUNCTION__ << "] " << host << ":" << port << std::endl;
        global_stream_lock.unlock();

        // Start the next receive
        Recv();
    }

    void OnConnect(const std::string& host, uint16_t port)
    {
        global_stream_lock.lock();
        std::cout << "[" << __FUNCTION__ << "] " << host << ":" << port << std::endl;
        global_stream_lock.unlock();

        // Start the next receive
        Recv();

        std::string str = "GET / HTTP/1.0\r\n\r\n";

        std::vector<uint8_t> request;
        std::copy(str.begin(), str.end(), std::back_inserter(request));
        Send(request);
    }

    void OnSend(const std::vector<uint8_t>& buffer)
    {
        global_stream_lock.lock();
        std::cout << "[" << __FUNCTION__ << "] " << buffer.size() << " bytes" << std::endl;

        for (size_t x = 0; x < buffer.size(); ++x)
        {
            std::cout << std::hex << std::setfill('0') << std::setw(2) << (int)buffer[x] << " ";

            if ((x + 1) % 16 == 0)
            {
                std::cout << std::endl;
            }
        }

        std::cout << std::endl;
        global_stream_lock.unlock();
    }

    void OnRecv(std::vector<uint8_t>& buffer)
    {
        global_stream_lock.lock();
        std::cout << "[" << __FUNCTION__ << "] " << buffer.size() << " bytes" << std::endl;

        for (size_t x = 0; x < buffer.size(); ++x)
        {
            std::cout << std::hex << std::setfill('0') << std::setw(2) << (int)buffer[x] << " ";

            if ((x + 1) % 16 == 0)
            {
                std::cout << std::endl;
            }
        }

        std::cout << std::endl;
        global_stream_lock.unlock();

        // Start the next receive
        Recv();
    }

    void OnTimer(const std::chrono::microseconds& delta)
    {
        global_stream_lock.lock();
        std::cout << "[" << __FUNCTION__ << "] " << delta.count() << std::endl;
        global_stream_lock.unlock();
    }

    void OnError(const asio::error_code& error)
    {
        global_stream_lock.lock();
        std::cout << "[" << __FUNCTION__ << "] " << error << std::endl;
        global_stream_lock.unlock();
    }

public:
    MyConnection(std::shared_ptr<Hive> hive) : Connection(hive)
    {
    }

    ~MyConnection()
    {
    }
};

int main(int argc, char* argv[])
{
    std::shared_ptr<Hive> hive(new Hive());

    std::shared_ptr<MyConnection> connection(new MyConnection(hive));
    connection->Connect("www.google.com", 80);

    char c;

    while (std::cin.get(c))
    {
        hive->Poll();
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    hive->Stop();

    return 0;
}
