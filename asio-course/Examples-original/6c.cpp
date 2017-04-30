#include <boost/asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <iostream>
#include <chrono>

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

void TimerHandler(
				  const boost::system::error_code & error, 
				  std::shared_ptr< boost::asio::deadline_timer > timer, 
				  std::shared_ptr< boost::asio::io_service::strand > strand
				  )
{
	if( error )
	{
		global_stream_lock.lock();
		std::cout << "[" << std::this_thread::get_id()
			<< "] Error: " << error << std::endl;
		global_stream_lock.unlock();
	}
	else
	{
		std::cout << "[" << std::this_thread::get_id()
			<< "] TimerHandler " << std::endl;

		timer->expires_from_now( boost::posix_time::seconds( 1 ) );
		timer->async_wait( 
			strand->wrap( std::bind( &TimerHandler, _1, timer, strand ) )
			);
	}
}

void PrintNum( int x )
{
	std::cout << "[" << std::this_thread::get_id()
		<< "] x: " << x << std::endl;
	std::this_thread::sleep_for( std::chrono::milliseconds( 1000 ) );
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

	std::this_thread::sleep_for( std::chrono::seconds( 1 ) );

	strand->post( std::bind( &PrintNum, 1 ) );
	strand->post( std::bind( &PrintNum, 2 ) );
	strand->post( std::bind( &PrintNum, 3 ) );
	strand->post( std::bind( &PrintNum, 4 ) );
	strand->post( std::bind( &PrintNum, 5 ) );

	std::shared_ptr< boost::asio::deadline_timer > timer(
		new boost::asio::deadline_timer( *io_service )
		);
	timer->expires_from_now( boost::posix_time::seconds( 1 ) );
	timer->async_wait( 
		strand->wrap( std::bind( &TimerHandler, _1, timer, strand ) )
		);

	std::cin.get();

	io_service->stop();

	for( int x = 0; x < 2; ++x )
	{
		worker_threads[x].join();
	}

	return 0;
}
