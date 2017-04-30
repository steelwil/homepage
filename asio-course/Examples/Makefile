#
# 'make depend' uses makedepend to automatically generate dependencies
#               (dependencies are added to end of Makefile)
# 'make'        build executable file 'mycc'
# 'make clean'  removes all .o and executable files
#

# define the C compiler to use
CC = g++

# define any compile-time flags
CFLAGS = -std=c++11 -c -Wall

# define any directories containing header files other than /usr/include
#
INCLUDES = -I/home/wil/projects/dev/Shared/asio-1.11.0/include

# define library paths in addition to /usr/lib
#   if I wanted to include libraries not in /usr/lib I'd specify
#   their path using -Lpath, something like:
LFLAGS =

# define any libraries to link into executable:
#   if I want to link in libraries (libx.so or libx.a) I use the -llibname
#   option, something like (this will link in libmylib.so and libm.so:
LIBS = -lpthread

# define the C source files
ifeq ($(MAKECMDGOALS),9a)
	SRCS = network.cpp $(MAKECMDGOALS).cpp
else ifeq ($(MAKECMDGOALS),9b)
	SRCS = network.cpp $(MAKECMDGOALS).cpp
else ifeq ($(MAKECMDGOALS),server)
	SRCS = network.cpp $(MAKECMDGOALS).cpp
else
	SRCS = $(MAKECMDGOALS).cpp
endif
# define the C object files
#
# This uses Suffix Replacement within a macro:
#   $(name:string1=string2)
#         For each word in 'name' replace 'string1' with 'string2'
# Below we are replacing the suffix .c of all words in the macro SRCS
# with the .o suffix
#
OBJS = $(SRCS:.cpp=.o)

# define the executable file
MAIN = $(MAKECMDGOALS)

#
# The following part of the makefile is generic; it can be used to
# build any executable just by changing the definitions above and by
# deleting dependencies appended to the file from 'make depend'
#

.PHONY: depend clean

all:    $(MAIN)
	@echo  $MAIN has been compiled

# linking
#$(CC) $@.o $(LFLAGS) $(LIBS) -o $@
#$(CC) $(OBJS) -o $(MAIN) $(LFLAGS) $(LIBS)
#$(CC) $(CFLAGS) $(INCLUDES) -o $(MAIN) $(OBJS) $(LFLAGS) $(LIBS)
$(MAIN): $(OBJS)
	$(CC) $(INCLUDES) -o $(MAIN) $(OBJS) $(LFLAGS) $(LIBS)

# this is a suffix replacement rule for building .o's from .c's
# it uses automatic variables $<: the name of the prerequisite of
# the rule(a .c file) and $@: the name of the target of the rule (a .o file)
# (see the gnu make manual section about automatic variables)
# compiling
.cpp.o:
	$(CC) $(CFLAGS) $(INCLUDES) -c $<  -o $@

clean:
	$(RM) *.o *~ $(MAIN)

depend: $(SRCS)
	makedepend $(INCLUDES) $^

# DO NOT DELETE THIS LINE -- make depend needs it
