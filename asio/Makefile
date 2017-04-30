# executable name
TARGET = server
# hearder files of project
DEPS = $(wildcard *.h)
# source files
SOURCES = $(wildcard *.cpp)
# include directories
ASIO_ROOT=/home/wil/projects/dev/Shared/asio-1.11.0/include
# library directories
#LDFLAGS := -L$(ASIO_ROOT)/stage/lib
# libraries
#LIBS = -lpthread
LIBS = -Wl,-Bstatic -Wl,-Bdynamic -lpthread
OBJECTS = $(SOURCES:.cpp=.o)

CC=g++
CFLAGS := -std=c++11 -c -Wall -I$(ASIO_ROOT)

all: $(TARGET)

$(MAKECMDGOALS) : $(MAKECMDGOALS).o
	$(CC) $@.o $(LDFLAGS) $(LIBS) -o $@

$(MAKECMDGOALS).o: $(MAKECMDGOALS).cpp $(DEPS)
	$(CC) $(CFLAGS) $< -o $@

#$(TARGET): $(OBJECTS)
#	$(CC) $(OBJECTS) $(LDFLAGS) $(LIBS) -o $@

##%.o: %.cpp $(DEPS)
##	$(CC) $(CFLAGS) $(SOURCES)
##$(OBJECTS) : %.o: %.cpp $(DEPS)
#%.o: %.cpp $(DEPS)
#	$(CC) $(CFLAGS) $< -o $@

.PHONY: clean
clean:
	rm *.o 1? 2? 3? 4? 5? 6? 7? 8? 9?


