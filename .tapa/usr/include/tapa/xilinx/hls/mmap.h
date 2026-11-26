#pragma once

#ifndef __SYNTHESIS__
#define __SYNTHESIS__
#endif

#include <cstddef>
#include <cstdint>
#include <hls_stream.h>

#include "tapa/xilinx/hls/stream.h"

namespace tapa {

template <typename T>
using mmap = T*;

template <typename T>
struct async_mmap {
  using addr_t = int64_t;
  using resp_t = uint8_t;

  hls::stream<addr_t> read_addr;
  hls::stream<T> read_data;
  hls::stream<addr_t> write_addr;
  hls::stream<T> write_data;
  hls::stream<resp_t> write_resp;
};

template <typename T, uint64_t S>
class mmaps;

template <typename T, int chan_count, int64_t chan_size>
class hmap;

}  // namespace tapa
