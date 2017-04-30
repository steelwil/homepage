//
// timer.cpp
// ~~~~~~~~~
//
// Copyright (c) 2003-2015 Christopher M. Kohlhoff (chris at kohlhoff dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// Performs a blocking wait of 5 seconds

#include <iostream>
#include <asio.hpp>
#include <chrono>
#include <asio/steady_timer.hpp>

int main()
{
  asio::io_service io;

  asio::steady_timer t(io);
  t.expires_from_now(std::chrono::seconds(5));
  t.wait();

  std::cout << "Hello, world!" << std::endl;

  return 0;
}
