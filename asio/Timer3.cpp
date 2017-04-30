//
// timer.cpp
// ~~~~~~~~~
//
// Copyright (c) 2003-2015 Christopher M. Kohlhoff (chris at kohlhoff dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// timer fires once a second, additional parameters are passed to the handler function

#include <iostream>
#include <functional>
#include <system_error>
#include <asio.hpp>
#include <asio/steady_timer.hpp>

void print(const std::error_code& /*e*/,
    asio::steady_timer* t, int* count)
{
  if (*count < 5)
  {
    std::cout << *count << std::endl;
    ++(*count);

    t->expires_at(t->expires_at() + std::chrono::seconds(1));
    t->async_wait(std::bind(print,
          std::placeholders::_1, t, count));
  }
}

int main()
{
  asio::io_service io;

  int count = 0;
  asio::steady_timer t(io);
  t.expires_from_now(std::chrono::seconds(1));
  t.async_wait(std::bind(&print,
        std::placeholders::_1, &t, &count));

  io.run();

  std::cout << "Final count is " << count << std::endl;

  return 0;
}
