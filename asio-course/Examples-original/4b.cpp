#include <boost/asio.hpp>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <iostream>
#include <chrono>

std::mutex global_stream_lock;

void WorkerThread( std::shared_ptr< boost::asio::io_service > io_service )
{
	global_stream_lock.lock();
	std::cout << "[" << std::this_thread::get_id() << "] Thread Start" << std::endl;
	global_stream_lock.unlock();

	io_service->run();

	global_stream_lock.lock();
	std::cout << "[" << std::this_thread::get_id()
		<< "] Thread Finish" << std::endl;
	global_stream_lock.unlock();
}

void PrintNum( int x )
{
	std::cout << "[" << std::this_thread::get_id() 
		<< "] x: " << x << std::endl;
}

int main( int argc, char * argv[] )
{
	std::shared_ptr< boost::asio::io_service > io_service(
		new boost::asio::io_service
		);
	std::shared_ptr< boost::asio::io_service::work > work(
		new boost::asio::io_service::work( *io_service )
		);
	boost::asio::io_service::strand strand( *io_service );

	global_stream_lock.lock();
	std::cout << "[" <<  std::this_thread::get_id()  
		<< "] The program will exit when all  work has finished." <<  std::endl;
	global_stream_lock.unlock();

	std::thread worker_threads[4];
	for( int x = 0; x < 4; ++x )
	{
		worker_threads[x] = std::thread( std::bind( &WorkerThread, io_service ) );
	}

	std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
	io_service->post( strand.wrap( std::bind( &PrintNum, 1 ) ) );
	io_service->post( strand.wrap( std::bind( &PrintNum, 2 ) ) );

	std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
	io_service->post( strand.wrap( std::bind( &PrintNum, 3 ) ) );
	io_service->post( strand.wrap( std::bind( &PrintNum, 4 ) ) );

	std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
	io_service->post( strand.wrap( std::bind( &PrintNum, 5 ) ) );
	io_service->post( strand.wrap( std::bind( &PrintNum, 6 ) ) );

	work.reset();

	for( int x = 0; x < 4; ++x )
	{
		worker_threads[x].join();
	}

	return 0;
}
