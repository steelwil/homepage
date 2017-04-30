#include <boost/asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <boost/bind.hpp>
#include <boost/lexical_cast.hpp>
#include <iostream>
#include <string>
#include <vector>
#include <list>
#include <iomanip>

//using namespace std::placeholders; // adds _1, _2, ...
std::mutex global_stream_lock;

void WorkerThread( std::shared_ptr< boost::asio::io_service > io_service )
{
	global_stream_lock.lock();
	std::cout << "[" << std::this_thread::get_id()
		<< "] Thread Start" << std::endl;
	global_stream_lock.unlock();

	while( true )
	{
		try
		{
			boost::system::error_code ec;
			io_service->run( ec );
			if( ec )
			{
				global_stream_lock.lock();
				std::cout << "[" << std::this_thread::get_id()
					<< "] Error: " << ec << std::endl;
				global_stream_lock.unlock();
			}
			break;
		}
		catch( std::exception & ex )
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

struct ClientContext : public std::enable_shared_from_this< ClientContext >
{
	boost::asio::ip::tcp::socket m_socket;
	
	std::vector< std::uint8_t > m_recv_buffer;
	size_t m_recv_buffer_index;

	std::list< std::vector< std::uint8_t > > m_send_buffer;

	ClientContext( boost::asio::io_service & io_service )
		: m_socket( io_service ), m_recv_buffer_index( 0 )
	{
		m_recv_buffer.resize( 4096 );
	}

	~ClientContext()
	{
	}

	void Close()
	{
		boost::system::error_code ec;
		m_socket.shutdown( boost::asio::ip::tcp::socket::shutdown_both, ec );
		m_socket.close( ec );
	}

	void OnSend( const boost::system::error_code & ec, std::list< std::vector< std::uint8_t > >::iterator itr )
	{
		if( ec )
		{
			global_stream_lock.lock();
			std::cout << "[" << std::this_thread::get_id()
				<< "] Error: " << ec << std::endl;
			global_stream_lock.unlock();

			Close();
		}
		else
		{
			global_stream_lock.lock();
			std::cout << "[" << std::this_thread::get_id()
				<< "] Sent " << (*itr).size() << " bytes." << std::endl;
			global_stream_lock.unlock();
		}
		m_send_buffer.erase( itr );

		// Start the next pending send
		if( !m_send_buffer.empty() )
		{
			boost::asio::async_write( 
				m_socket, 
				boost::asio::buffer( m_send_buffer.front() ), 
				boost::bind( 
					&ClientContext::OnSend, 
					shared_from_this(), 
					boost::asio::placeholders::error, 
					m_send_buffer.begin()
				)
			);
		}
	}

	void Send( const void * buffer, size_t length )
	{
		bool can_send_now = false;

		std::vector< std::uint8_t > output;
		std::copy( (const std::uint8_t *)buffer, (const std::uint8_t *)buffer + length, std::back_inserter( output ) );

		// Store if this is the only current send or not
		can_send_now = m_send_buffer.empty();

		// Save the buffer to be sent
		m_send_buffer.push_back( output );

		// Only send if there are no more pending buffers waiting!
		if( can_send_now )
		{
			// Start the next pending send
			boost::asio::async_write( 
				m_socket, 
				boost::asio::buffer( m_send_buffer.front() ), 
				boost::bind( 
					&ClientContext::OnSend, 
					shared_from_this(), 
					boost::asio::placeholders::error, 
					m_send_buffer.begin()
				)
			);
		}
	}

	void OnRecv( const boost::system::error_code & ec, size_t bytes_transferred )
	{
		if( ec )
		{
			global_stream_lock.lock();
			std::cout << "[" << std::this_thread::get_id()
				<< "] Error: " << ec << std::endl;
			global_stream_lock.unlock();

			Close();
		}
		else
		{
			// Increase how many bytes we have saved up
			m_recv_buffer_index += bytes_transferred;

			// Debug information
			global_stream_lock.lock();
			std::cout << "[" << std::this_thread::get_id()
				<< "] Recv " << bytes_transferred << " bytes." << std::endl;
			global_stream_lock.unlock();

			// Dump all the data
			global_stream_lock.lock();
			for( size_t x = 0; x < m_recv_buffer_index; ++x )
			{
				std::cout << std::hex << std::setfill( '0' ) << 
					std::setw( 2 ) << (int)m_recv_buffer[ x ] << " ";
				if( ( x + 1 ) % 16 == 0 )
				{
					std::cout << std::endl;
				}
			}
			std::cout << std::endl << std::dec;
			global_stream_lock.unlock();

			// Discard all the data (virtually, not physically!)
			m_recv_buffer_index = 0;

			// Start the next recv cycle
			Recv();
		}
	}

	void Recv()
	{
		m_socket.async_read_some( 
			boost::asio::buffer( 
				&m_recv_buffer[ m_recv_buffer_index ], 
				m_recv_buffer.size() - m_recv_buffer_index ), 
			boost::bind( &ClientContext::OnRecv, shared_from_this(), _1, _2 )
		);
	}
};

void OnAccept( const boost::system::error_code & ec, std::shared_ptr< ClientContext > client )
{
	if( ec )
	{
		global_stream_lock.lock();
		std::cout << "[" << std::this_thread::get_id()
			<< "] Error: " << ec << std::endl;
		global_stream_lock.unlock();
	}
	else
	{
		global_stream_lock.lock();
		std::cout << "[" << std::this_thread::get_id()
			<< "] Accepted!" << std::endl;
		global_stream_lock.unlock();

		// 2 bytes message size, followed by the message
		client->Send( "\x02\x00Hi", 6 );
		client->Recv();
	}
}

int main( int argc, char * argv[] )
{
	std::shared_ptr< boost::asio::io_service > io_service(
		new boost::asio::io_service
		);
	std::shared_ptr< boost::asio::io_service::work > work(
		new boost::asio::io_service::work( *io_service )
		);
	std::shared_ptr< boost::asio::io_service::strand > strand(
		new boost::asio::io_service::strand( *io_service )
		);

	global_stream_lock.lock();
	std::cout << "[" << std::this_thread::get_id()
		<< "] Press [return] to exit." << std::endl;
	global_stream_lock.unlock();

	// 1 worker thread so we do not have to deal with thread safety issues
	std::thread worker_threads[1];
	for( int x = 0; x < 1; ++x )
	{
		worker_threads[x] = std::thread( std::bind( &WorkerThread, io_service ) );
	}

	std::shared_ptr< boost::asio::ip::tcp::acceptor > acceptor(
		new boost::asio::ip::tcp::acceptor( *io_service )
		);
	std::shared_ptr< ClientContext > client(
		new ClientContext( *io_service )
		);

	try
	{
		boost::asio::ip::tcp::resolver resolver( *io_service );
		boost::asio::ip::tcp::resolver::query query( 
			"127.0.0.1", 
			boost::lexical_cast< std::string >( 7777 )
			);
		boost::asio::ip::tcp::endpoint endpoint = *resolver.resolve( query );
		acceptor->open( endpoint.protocol() );
		acceptor->set_option( boost::asio::ip::tcp::acceptor::reuse_address( false ) );
		acceptor->bind( endpoint );
		acceptor->listen( boost::asio::socket_base::max_connections );
		acceptor->async_accept( client->m_socket, boost::bind( OnAccept, _1, client ) );

		global_stream_lock.lock();
		std::cout << "Listening on: " << endpoint << std::endl;
		global_stream_lock.unlock();
	}
	catch( std::exception & ex )
	{
		global_stream_lock.lock();
		std::cout << "[" << std::this_thread::get_id()
			<< "] Exception: " << ex.what() << std::endl;
		global_stream_lock.unlock();
	}

	std::cin.get();

	boost::system::error_code ec;
	acceptor->close( ec );

	io_service->stop();

	for( int x = 0; x < 1; ++x )
	{
		worker_threads[x].join();
	}

	return 0;
}
