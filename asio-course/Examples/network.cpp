#include <atomic>
#include "network.h"
#include <functional>

using namespace std::placeholders; // adds _1, _2, ...

//-----------------------------------------------------------------------------

Hive::Hive()
    : m_work_ptr(new asio::io_service::work(m_io_service))
    , m_shutdown(0)
{
}

Hive::~Hive()
{
}

asio::io_service& Hive::GetService()
{
    return m_io_service;
}

bool Hive::HasStopped()
{
    int expected = 1;
    return (std::atomic_compare_exchange_strong(&m_shutdown, &expected, 1));
}

void Hive::Poll()
{
    m_io_service.poll();
}

void Hive::Run()
{
    m_io_service.run();
}

void Hive::Stop()
{
    int expected = 1;

    if (std::atomic_compare_exchange_strong(&m_shutdown, &expected, 0) == 0)
    {
        m_work_ptr.reset();
        m_io_service.run();
        m_io_service.stop();
    }
}

void Hive::Reset()
{
    int expected = 0;

    if (std::atomic_compare_exchange_strong(&m_shutdown, &expected, 1) == 1)
    {
        m_io_service.reset();
        m_work_ptr.reset(new asio::io_service::work(m_io_service));
    }
}

//-----------------------------------------------------------------------------

Acceptor::Acceptor(std::shared_ptr<Hive> hive)
    : m_hive(hive)
    , m_acceptor(hive->GetService())
    , m_io_strand(hive->GetService())
    , m_timer(hive->GetService())
    , m_timer_interval(1000)
    , m_error_state(0)
{
}

Acceptor::~Acceptor()
{
}

void Acceptor::StartTimer()
{
    m_last_time = std::chrono::steady_clock::now();
    m_timer.expires_from_now(std::chrono::milliseconds(m_timer_interval));
    m_timer.async_wait(m_io_strand.wrap(std::bind(&Acceptor::HandleTimer, shared_from_this(), _1)));
}

void Acceptor::StartError(const std::error_code& error)
{
    int expected = 1;

    if (std::atomic_compare_exchange_strong(&m_error_state, &expected, 0) == 0)
    {
        std::error_code ec;
        m_acceptor.cancel(ec);
        m_acceptor.close(ec);
        m_timer.cancel(ec);
        OnError(error);
    }
}

void Acceptor::DispatchAccept(std::shared_ptr<Connection> connection)
{
    m_acceptor.async_accept(
        connection->GetSocket(),
        connection->GetStrand().wrap(std::bind(&Acceptor::HandleAccept, shared_from_this(), _1, connection)));
}

void Acceptor::HandleTimer(const std::error_code& error)
{
    if (error || HasError() || m_hive->HasStopped())
    {
        StartError(error);
    }
    else
    {
        auto dur = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - m_last_time);
        OnTimer(dur);
        StartTimer();
    }
}

void Acceptor::HandleAccept(const std::error_code& error, std::shared_ptr<Connection> connection)
{
    if (error || HasError() || m_hive->HasStopped())
    {
        connection->StartError(error);
    }
    else
    {
        if (connection->GetSocket().is_open())
        {
            connection->StartTimer();

            if (OnAccept(connection,
                         connection->GetSocket().remote_endpoint().address().to_string(),
                         connection->GetSocket().remote_endpoint().port()))
            {
                connection->OnAccept(m_acceptor.local_endpoint().address().to_string(),
                                     m_acceptor.local_endpoint().port());
            }
        }
        else
        {
            StartError(error);
        }
    }
}

void Acceptor::Stop()
{
    m_io_strand.post(std::bind(&Acceptor::HandleTimer, shared_from_this(), asio::error::connection_reset));
}

void Acceptor::Accept(std::shared_ptr<Connection> connection)
{
    m_io_strand.post(std::bind(&Acceptor::DispatchAccept, shared_from_this(), connection));
}

void Acceptor::Listen(const std::string& host, const uint16_t& port)
{
    asio::ip::tcp::resolver resolver(m_hive->GetService());
    asio::ip::tcp::resolver::query query(host, std::to_string(port));
    asio::ip::tcp::endpoint endpoint = *resolver.resolve(query);
    m_acceptor.open(endpoint.protocol());
    m_acceptor.set_option(asio::ip::tcp::acceptor::reuse_address(false));
    m_acceptor.bind(endpoint);
    m_acceptor.listen(asio::socket_base::max_connections);
    StartTimer();
}

std::shared_ptr<Hive> Acceptor::GetHive()
{
    return m_hive;
}

asio::ip::tcp::acceptor& Acceptor::GetAcceptor()
{
    return m_acceptor;
}

int32_t Acceptor::GetTimerInterval() const
{
    return m_timer_interval;
}

void Acceptor::SetTimerInterval(int32_t timer_interval)
{
    m_timer_interval = timer_interval;
}

bool Acceptor::HasError()
{
    int expected = 1;
    return (std::atomic_compare_exchange_strong(&m_error_state, &expected, 1) == 1);
}

//-----------------------------------------------------------------------------

Connection::Connection(std::shared_ptr<Hive> hive)
    : m_hive(hive)
    , m_socket(hive->GetService())
    , m_io_strand(hive->GetService())
    , m_timer(hive->GetService())
    , m_receive_buffer_size(4096)
    , m_timer_interval(1000)
    , m_error_state(0)
{
}

Connection::~Connection()
{
}

void Connection::Bind(const std::string& ip, uint16_t port)
{
    asio::ip::tcp::endpoint endpoint(asio::ip::address::from_string(ip), port);
    m_socket.open(endpoint.protocol());
    m_socket.set_option(asio::ip::tcp::acceptor::reuse_address(false));
    m_socket.bind(endpoint);
}

void Connection::StartSend()
{
    if (!m_pending_sends.empty())
    {
        asio::async_write(
            m_socket,
            asio::buffer(m_pending_sends.front()),
            m_io_strand.wrap(std::bind(
                                 &Connection::HandleSend, shared_from_this(), _1, m_pending_sends.begin())));
    }
}

void Connection::StartRecv(int32_t total_bytes)
{
    if (total_bytes > 0)
    {
        m_recv_buffer.resize(total_bytes);
        asio::async_read(m_socket,
                         asio::buffer(m_recv_buffer),
                         m_io_strand.wrap(std::bind(&Connection::HandleRecv, shared_from_this(), _1, _2)));
    }
    else
    {
        m_recv_buffer.resize(m_receive_buffer_size);
        m_socket.async_read_some(asio::buffer(m_recv_buffer),
                                 m_io_strand.wrap(std::bind(&Connection::HandleRecv, shared_from_this(), _1, _2)));
    }
}

void Connection::StartTimer()
{
    m_last_time = std::chrono::steady_clock::now();
    m_timer.expires_from_now(std::chrono::milliseconds(m_timer_interval));
    m_timer.async_wait(m_io_strand.wrap(std::bind(&Connection::DispatchTimer, shared_from_this(), _1)));
}

void Connection::StartError(const std::error_code& error)
{
    int expected = 1;

    if (std::atomic_compare_exchange_strong(&m_error_state, &expected, 0) == 0)
    {
        asio::error_code ec;
        m_socket.shutdown(asio::ip::tcp::socket::shutdown_both, ec);
        m_socket.close(ec);
        m_timer.cancel(ec);
        OnError(error);
    }
}

void Connection::HandleConnect(const std::error_code& error)
{
    if (error || HasError() || m_hive->HasStopped())
    {
        StartError(error);
    }
    else
    {
        if (m_socket.is_open())
        {
            OnConnect(m_socket.remote_endpoint().address().to_string(), m_socket.remote_endpoint().port());
        }
        else
        {
            StartError(error);
        }
    }
}

void Connection::HandleSend(const std::error_code& error, std::list<std::vector<uint8_t> >::iterator itr)
{
    if (error || HasError() || m_hive->HasStopped())
    {
        StartError(error);
    }
    else
    {
        OnSend(*itr);
        m_pending_sends.erase(itr);
        StartSend();
    }
}

void Connection::HandleRecv(const std::error_code& error, int32_t actual_bytes)
{
    if (error || HasError() || m_hive->HasStopped())
    {
        StartError(error);
    }
    else
    {
        m_recv_buffer.resize(actual_bytes);
        OnRecv(m_recv_buffer);
        m_pending_recvs.pop_front();

        if (!m_pending_recvs.empty())
        {
            StartRecv(m_pending_recvs.front());
        }
    }
}

void Connection::HandleTimer(const std::error_code& error)
{
    if (error || HasError() || m_hive->HasStopped())
    {
        StartError(error);
    }
    else
    {
        auto dur = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - m_last_time);
        OnTimer(dur);
        StartTimer();
    }
}

void Connection::DispatchSend(std::vector<uint8_t> buffer)
{
    bool should_start_send = m_pending_sends.empty();
    m_pending_sends.push_back(buffer);

    if (should_start_send)
    {
        StartSend();
    }
}

void Connection::DispatchRecv(int32_t total_bytes)
{
    bool should_start_receive = m_pending_recvs.empty();
    m_pending_recvs.push_back(total_bytes);

    if (should_start_receive)
    {
        StartRecv(total_bytes);
    }
}

void Connection::DispatchTimer(const std::error_code& error)
{
    m_io_strand.post(std::bind(&Connection::HandleTimer, shared_from_this(), error));
}

void Connection::Connect(const std::string& host, uint16_t port)
{
    std::error_code ec;
    asio::ip::tcp::resolver resolver(m_hive->GetService());
    asio::ip::tcp::resolver::query query(host, std::to_string(port));
    asio::ip::tcp::resolver::iterator iterator = resolver.resolve(query);
    m_socket.async_connect(*iterator, m_io_strand.wrap(std::bind(&Connection::HandleConnect, shared_from_this(), _1)));
    StartTimer();
}

void Connection::Disconnect()
{
    m_io_strand.post(std::bind(&Connection::HandleTimer, shared_from_this(), asio::error::connection_reset));
}

void Connection::Recv(int32_t total_bytes)
{
    m_io_strand.post(std::bind(&Connection::DispatchRecv, shared_from_this(), total_bytes));
}

void Connection::Send(const std::vector<uint8_t>& buffer)
{
    m_io_strand.post(std::bind(&Connection::DispatchSend, shared_from_this(), buffer));
}

asio::ip::tcp::socket& Connection::GetSocket()
{
    return m_socket;
}

asio::io_service::strand& Connection::GetStrand()
{
    return m_io_strand;
}

std::shared_ptr<Hive> Connection::GetHive()
{
    return m_hive;
}

void Connection::SetReceiveBufferSize(int32_t size)
{
    m_receive_buffer_size = size;
}

int32_t Connection::GetReceiveBufferSize() const
{
    return m_receive_buffer_size;
}

int32_t Connection::GetTimerInterval() const
{
    return m_timer_interval;
}

void Connection::SetTimerInterval(int32_t timer_interval)
{
    m_timer_interval = timer_interval;
}

bool Connection::HasError()
{
    int expected = 1;
    return (std::atomic_compare_exchange_strong(&m_error_state, &expected, 1) == 1);
}

//-----------------------------------------------------------------------------
