# executable name
TARGET = server
# hearder files of project
DEPS = $(wildcard *.h)
# source files
SOURCES = $(wildcard *.cpp)
# include directories
BOOST_ROOT=/home/wil/projects/dev/Shared/boost_1_58_0
# library directories
LDFLAGS := -L$(BOOST_ROOT)/stage/lib
# libraries
#LIBS = -lpthread
LIBS = -Wl,-Bstatic -lboost_system -Wl,-Bdynamic -lpthread
OBJECTS = $(SOURCES:.cpp=.o)

CC=g++
CFLAGS := -std=c++11 -c -Wall -I$(BOOST_ROOT)

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


