# tests/Makefile — builds and runs host-side tests.
# Distributed under the terms of the MIT License.

CXX      := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -I../src
BUILDDIR := ../build/tests

SRCS     := ../src/hw/*.cpp

.PHONY: all clean

all: $(BUILDDIR)/test_registerio $(BUILDDIR)/d1_accept $(BUILDDIR)/test_pushbuffer $(BUILDDIR)/d3_accept
	@$(BUILDDIR)/test_registerio
	@$(BUILDDIR)/d1_accept
	@$(BUILDDIR)/test_pushbuffer
	@$(BUILDDIR)/d3_accept

$(BUILDDIR)/test_registerio: test_registerio.cpp ../src/hw/RegisterIO.h ../src/hw/RegisterIO.cpp | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) test_registerio.cpp $(SRCS) -o $@

$(BUILDDIR)/d1_accept: accept/d1_accept.cpp ../src/hw/RegisterIO.h ../src/hw/RegisterIO.cpp | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) accept/d1_accept.cpp $(SRCS) -o $@

$(BUILDDIR)/test_pushbuffer: test_pushbuffer.cpp ../src/fifo/PushBuffer.h ../src/fifo/PushBuffer.cpp | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) test_pushbuffer.cpp ../src/fifo/*.cpp -o $@

$(BUILDDIR)/d3_accept: accept/d3_accept.cpp ../src/fifo/PushBuffer.h ../src/fifo/PushBuffer.cpp | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) accept/d3_accept.cpp ../src/fifo/*.cpp -o $@

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

clean:
	rm -rf $(BUILDDIR)
