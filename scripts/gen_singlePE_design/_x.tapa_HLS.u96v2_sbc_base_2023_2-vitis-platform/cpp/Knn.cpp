#include "knn.h"
#define printf(...) ((void)0)
#define absval(input)                                                          \
  ((input) > 0 ? static_cast<DATA_TYPE>(input)                                 \
               : static_cast<DATA_TYPE>(-1 * (input)))
#define SORT_TO_HIERMERGE_STREAM_ARGS(PE) L0_out_dist_##PE, L0_out_id_##PE
#define INVOKE_PPS_UNITS_FOR_PE(PE)                                            \
  .invoke(para_partial_sort, PE, compute_to_sort_stream_##PE,                  \
          SORT_TO_HIERMERGE_STREAM_ARGS(PE))

void load_KNN(int debug_PE_ID, tapa::async_mmap<INTERFACE_WIDTH> &searchSpace,
              tapa::ostream<INTERFACE_WIDTH> &load_to_compute_stream);
void compute_KNN(int debug_pe_idx, int debug_start_idx,
                 tapa::istream<INTERFACE_WIDTH> &load_to_compute_stream,
                 tapa::ostream<DATA_TYPE> &compute_to_sort_stream);
void para_partial_sort(const int PE_idx,
                       tapa::istream<INTERFACE_WIDTH> &compute_to_sort_stream_0,
                       tapa::ostream<DATA_TYPE> &sort_to_hiermerge_dist_stream,
                       tapa::ostream<int> &sort_to_hiermerge_id_stream);
void krnl_singlePE_Write_Outputs(tapa::istream<DATA_TYPE> &in_dist0,
                                 tapa::istream<int> &in_id0,
                                 tapa::async_mmap<INT32> &output_knn);

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