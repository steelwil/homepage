//
// timer.cpp
// ~~~~~~~~~
//
// Copyright (c) 2003-2015 Christopher M. Kohlhoff (chris at kohlhoff dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//

#include <iostream>
#include <asio.hpp>
#include <functional>
#include <chrono>
#include <asio/steady_timer.hpp>

class printer
{
public:
  printer(asio::io_service& io)
    : timer_(io, std::chrono::seconds(1)),
      count_(0)
  {
    timer_.async_wait(std::bind(&printer::print, this));
  }

  ~printer()
  {
    std::cout << "Final count is " << count_ << std::endl;
  }

  void print()
  {
    if (count_ < 5)
    {
      std::cout << count_ << std::endl;
      ++count_;

      timer_.expires_at(timer_.expires_at() + std::chrono::seconds(1));
      timer_.async_wait(std::bind(&printer::print, this));
    }
  }

private:
  asio::steady_timer timer_;
  int count_;
};

int main()
{
  asio::io_service io;
  printer p(io);
  io.run();

  return 0;
}
