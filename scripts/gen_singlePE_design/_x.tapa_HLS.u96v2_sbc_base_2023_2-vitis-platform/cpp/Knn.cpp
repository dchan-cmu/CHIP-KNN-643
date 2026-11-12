#include "knn.h"
#define printf(...) ((void)0)
#define absval(input)                                                          \
  ((input) > 0 ? static_cast<DATA_TYPE>(input)                                 \
               : static_cast<DATA_TYPE>(-1 * (input)))

void Knn(tapa::mmap<INTERFACE_WIDTH> in_0, tapa::mmap<INT32> final_out) {
#pragma HLS interface m_axi port = in_0 offset = slave bundle = gmem0
#pragma HLS interface m_axi port = final_out offset = slave bundle = gmem1
#pragma HLS interface s_axilite port = return bundle = control
}
