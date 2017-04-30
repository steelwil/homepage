#include <boost/asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <iostream>

std::mutex global_stream_lock;

void WorkerThread( std::shared_ptr< boost::asio::io_service > io_service )
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

size_t fib( size_t n )
{
	if ( n <= 1 )
	{
		return n;
	}
	std::this_thread::sleep_for( 
		std::chrono::milliseconds( 1000 )
	    );
	return fib( n - 1 ) + fib( n - 2);
}

void CalculateFib( size_t n )
{
	global_stream_lock.lock();
	std::cout << "[" << std::this_thread::get_id()
		<< "] Now calculating fib( " << n << " ) " << std::endl;
	global_stream_lock.unlock();

	size_t f = fib( n );

	global_stream_lock.lock();
	std::cout << "[" << std::this_thread::get_id()
		<< "] fib( " << n << " ) = " << f << std::endl;
	global_stream_lock.unlock();
}

int main( int argc, char * argv[] )
{
	std::shared_ptr< boost::asio::io_service > io_service(
		new boost::asio::io_service
		);
	std::shared_ptr< boost::asio::io_service::work > work(
		new boost::asio::io_service::work( *io_service )
		);

	global_stream_lock.lock();
	std::cout << "[" << std::this_thread::get_id()
		<< "] The program will exit when all work has finished."
		<< std::endl;
	global_stream_lock.unlock();

	std::thread worker_threads[2];
	for( int x = 0; x < 2; ++x )
	{
		worker_threads[x] = std::thread(std::bind(&WorkerThread, io_service));
	}

	io_service->post( std::bind( CalculateFib, 3 ) );
	io_service->post( std::bind( CalculateFib, 4 ) );
	io_service->post( std::bind( CalculateFib, 5 ) );

	work.reset();

	for( int x = 0; x < 2; ++x )
	{
		worker_threads[x].join();
	}

	return 0;
}
