#include "knn.h"
#define printf(...) ((void)0)
#define absval(input)                                                          \
  ((input) > 0 ? static_cast<DATA_TYPE>(input)                                 \
               : static_cast<DATA_TYPE>(-1 * (input)))

void Knn(tapa::mmap<INTERFACE_WIDTH> in_0, tapa::mmap<INT32> final_out) {

  // Streams, for the global merge:
  tapa::stream<DATA_TYPE, TOP> L0_out_dist_0;
  tapa::stream<int, TOP> L0_out_id_0;
  // Streams, for load->compute->sort:
  tapa::stream<INTERFACE_WIDTH, 2> load_to_compute_stream_0;
  tapa::stream<DATA_TYPE, 2> compute_to_sort_stream_0;

  tapa::task()
      .invoke(load_KNN, 0, in_0, load_to_compute_stream_0)

      .invoke(compute_KNN, 0, NUM_SP_PTS_PER_KRNL_PADDED * 0,
              load_to_compute_stream_0, compute_to_sort_stream_0)

          INVOKE_PPS_UNITS_FOR_PE(0)

      ////////// MERGING LOGIC

      // INTER-PE HIERMERGE:
      .invoke(krnl_singlePE_Write_Outputs, L0_out_dist_0, L0_out_id_0,
              final_out);
}