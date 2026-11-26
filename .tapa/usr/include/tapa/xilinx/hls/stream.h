#pragma once

#ifndef __SYNTHESIS__
#define __SYNTHESIS__
#endif

#include "tapa/base/stream.h"

#include <cassert>
#include <cstddef>
#include <cstdint>

#include <hls_stream.h>

namespace tapa {

template <typename T, uint64_t N = kStreamDefaultDepth,
          uint64_t SimulationDepth = N>
using stream = hls::stream<T, int(N)>;

template <typename T>
using istream = hls::stream<T>;

template <typename T>
using ostream = hls::stream<T>;

template <typename T, uint64_t S>
using istreams = istream<T>[S];

template <typename T, uint64_t S>
using ostreams = ostream<T>[S];

template <typename T, uint64_t S, uint64_t N = kStreamDefaultDepth,
          uint64_t SimulationDepth = N>
using streams = stream<T, N>[S];

}  // namespace tapa
