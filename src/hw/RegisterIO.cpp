// RegisterIO.cpp — implementations
// Task D1.
// Distributed under the terms of the MIT License.

#include "hw/RegisterIO.h"

#include <sstream>
#include <iomanip>

namespace k40 {

// ---- RegisterIO ----

uint32_t RegisterIO::mask32(uint32_t offset, uint32_t mask, uint32_t value)
{
	uint32_t old = read32(offset);
	write32(offset, (old & ~mask) | value);
	return old;
}

// ---- MockMMIO ----

MockMMIO::MockMMIO(uint32_t size)
	: fSize(size & ~3u),	// whole registers only
	  fMemory(size / 4, 0u)
{
}

void MockMMIO::checkBounds(uint32_t offset) const
{
	if (offset >= fSize || offset % 4 != 0)
		throw std::out_of_range("MockMMIO offset out of range or not aligned");
}

void MockMMIO::poke(uint32_t offset, uint32_t value)
{
	checkBounds(offset);
	fMemory[offset / 4] = value;
}

uint32_t MockMMIO::peek(uint32_t offset) const
{
	checkBounds(offset);
	return fMemory[offset / 4];
}

uint32_t MockMMIO::read32(uint32_t offset)
{
	checkBounds(offset);
	uint32_t val = fMemory[offset / 4];
	// Call read hook if registered (hook does not change stored value)
	auto it = fReadHooks.find(offset);
	if (it != fReadHooks.end())
		val = it->second(val);

	fLog.push_back({Access::READ, offset, val});
	return val;
}

void MockMMIO::write32(uint32_t offset, uint32_t value)
{
	checkBounds(offset);
	fMemory[offset / 4] = value;
	fLog.push_back({Access::WRITE, offset, value});

	// Call write hook after storing
	auto it = fWriteHooks.find(offset);
	if (it != fWriteHooks.end())
		it->second(*this, value);
}

std::vector<Access> MockMMIO::log() const
{
	return fLog;
}

void MockMMIO::clearLog()
{
	fLog.clear();
}

void MockMMIO::onRead(uint32_t offset, std::function<uint32_t(uint32_t)> hook)
{
	fReadHooks[offset] = hook;
}

void MockMMIO::onWrite(uint32_t offset,
                       std::function<void(MockMMIO&, uint32_t)> hook)
{
	fWriteHooks[offset] = hook;
}

// ---- TraceMismatch ----

static std::string formatTraceMismatchMsg(size_t index, uint32_t offset)
{
	std::ostringstream oss;
	oss << "TraceMismatch at index " << index
	    << " offset 0x" << std::hex << std::setfill('0') << std::setw(6)
	    << offset;
	return oss.str();
}

TraceMismatch::TraceMismatch(size_t index, uint32_t offset)
	: std::runtime_error(formatTraceMismatchMsg(index, offset)),
	  fIndex(index)
{
}

size_t TraceMismatch::index() const
{
	return fIndex;
}

// ---- TraceMMIO ----

TraceMMIO::TraceMMIO(std::vector<Access> expected)
	: fExpected(std::move(expected)),
	  fPos(0)
{
}

uint32_t TraceMMIO::read32(uint32_t offset)
{
	if (fPos >= fExpected.size())
		throw TraceMismatch(fPos, offset);

	const Access& a = fExpected[fPos];
	if (a.op != Access::READ || a.offset != offset)
		throw TraceMismatch(fPos, offset);

	fPos++;
	return a.value;
}

void TraceMMIO::write32(uint32_t offset, uint32_t value)
{
	if (fPos >= fExpected.size())
		throw TraceMismatch(fPos, offset);

	const Access& a = fExpected[fPos];
	if (a.op != Access::WRITE || a.offset != offset || a.value != value)
		throw TraceMismatch(fPos, offset);

	fPos++;
}

bool TraceMMIO::done() const
{
	return fPos >= fExpected.size();
}

size_t TraceMMIO::position() const
{
	return fPos;
}

// ---- Trace parsing ----

std::vector<Access> parseTrace(std::istream& in)
{
	std::vector<Access> result;
	std::string line;

	while (std::getline(in, line)) {
		// Drop a comment, then skip lines with nothing left
		std::string::size_type hash = line.find('#');
		if (hash != std::string::npos)
			line.erase(hash);
		if (line.find_first_not_of(" \t\r") == std::string::npos)
			continue;

		std::istringstream ss(line);
		char type;
		std::string offsetStr, valueStr;
		if (!(ss >> type >> offsetStr >> valueStr))
			throw std::invalid_argument("parseTrace: bad line");

		if (type != 'R' && type != 'W')
			throw std::invalid_argument("parseTrace: bad type");

		// Reject negative tokens explicitly: stoull accepts a minus and wraps modulo 2^64.
		if (offsetStr[0] == '-' || valueStr[0] == '-')
			throw std::invalid_argument("parseTrace: negative hexadecimal token");

		// F7: parse with stoull and pos; reject out-of-range, partial tokens
		std::size_t pos = 0;
		uint64_t offsetVal = std::stoull(offsetStr, &pos, 16);
		if (pos != offsetStr.size())
			throw std::invalid_argument("parseTrace: partial offset token");
		if (offsetVal > 0xffffffffULL)
			throw std::invalid_argument("parseTrace: offset exceeds 32 bits");

		pos = 0;
		uint64_t valueVal = std::stoull(valueStr, &pos, 16);
		if (pos != valueStr.size())
			throw std::invalid_argument("parseTrace: partial value token");
		if (valueVal > 0xffffffffULL)
			throw std::invalid_argument("parseTrace: value exceeds 32 bits");

		// Check for trailing tokens after the value
		std::string trailing;
		if (ss >> trailing) {
			// Allowed if the trailing token starts with '#'
			if (trailing[0] != '#')
				throw std::invalid_argument("parseTrace: trailing token after value");
		}

		Access a;
		a.op = type == 'R' ? Access::READ : Access::WRITE;
		a.offset = static_cast<uint32_t>(offsetVal);
		a.value = static_cast<uint32_t>(valueVal);

		result.push_back(a);
	}

	return result;
}

std::string formatTrace(const std::vector<Access>& t)
{
	std::ostringstream oss;
	for (const auto& a : t) {
		oss << (a.op == Access::READ ? "R" : "W")
		    << " 0x" << std::hex << std::setfill('0') << std::setw(6)
		    << a.offset
		    << " 0x" << std::setw(8) << a.value << "\n";
	}
	return oss.str();
}

} // namespace k40
