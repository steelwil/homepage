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

void OnConnect( const boost::system::error_code & ec, std::shared_ptr< boost::asio::ip::tcp::socket > sock )
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
			<< "] Connected!" << std::endl;
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

	std::shared_ptr< boost::asio::ip::tcp::socket > sock(
		new boost::asio::ip::tcp::socket( *io_service )
		);

	try
	{
		boost::asio::ip::tcp::resolver resolver( *io_service );
		boost::asio::ip::tcp::resolver::query query( 
			"www.google.com", 
			boost::lexical_cast< std::string >( 80 )
			);
		boost::asio::ip::tcp::resolver::iterator iterator = resolver.resolve( query );
		boost::asio::ip::tcp::endpoint endpoint = *iterator;

		global_stream_lock.lock();
		std::cout << "Connecting to: " << endpoint << std::endl;
		global_stream_lock.unlock();

		sock->async_connect( endpoint, std::bind( OnConnect, _1, sock ) );
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
	sock->shutdown( boost::asio::ip::tcp::socket::shutdown_both, ec );
	sock->close( ec );

	io_service->stop();

	for( int x = 0; x < 2; ++x )
	{
		worker_threads[x].join();
	}

	return 0;
}
