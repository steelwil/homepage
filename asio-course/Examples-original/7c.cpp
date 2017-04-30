#include <boost/asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <boost/lexical_cast.hpp>
#include <iostream>
#include <string>

using namespace std::placeholders; // adds _1, _2, ...
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

void OnAccept( const boost::system::error_code & ec, std::shared_ptr< boost::asio::ip::tcp::socket > sock )
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

	std::thread worker_threads[2];
	for( int x = 0; x < 2; ++x )
	{
		worker_threads[x] = std::thread( std::bind( &WorkerThread, io_service ) );
	}

	std::shared_ptr< boost::asio::ip::tcp::acceptor > acceptor(
		new boost::asio::ip::tcp::acceptor( *io_service )
		);
	std::shared_ptr< boost::asio::ip::tcp::socket > sock(
		new boost::asio::ip::tcp::socket( *io_service )
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
		acceptor->async_accept( *sock, std::bind( OnAccept, _1, sock ) );

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

	sock->shutdown( boost::asio::ip::tcp::socket::shutdown_both, ec );
	sock->close( ec );

	io_service->stop();

	for( int x = 0; x < 2; ++x )
	{
		worker_threads[x].join();
	}

	return 0;
}
