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

void krnl_singlePE_Write_Outputs(tapa::istream<DATA_TYPE> &in_dist0,
                                 tapa::istream<int> &in_id0,
                                 tapa::async_mmap<INT32> &output_knn) {
  DATA_TYPE cur_dist;
  int cur_id;
  int i_req_output = 2 * TOP - 1;
  int i_resp_output = 2 * TOP - 1;
  for (int i = 0; i < TOP; ++i) {
#pragma HLS pipeline II = 1
    cur_dist = in_dist0.read();
    cur_id = in_id0.read();
    INT32 outval = 0;
    if (i_req_output < 2 * TOP && i_req_output >= 0 &&
        !output_knn.write_addr.full() && !output_knn.write_data.full()) {
      outval.range(DATA_TYPE_TOTAL_SZ - 1, 0) =
          cur_dist.range(DATA_TYPE_TOTAL_SZ - 1, 0);
      output_knn.write_addr.write(i_req_output * sizeof(INT32));
      output_knn.write_data.write(outval);
      --i_req_output;
    }
    if (!output_knn.write_resp.empty()) {
      i_resp_output += (unsigned int)(output_knn.write_resp.read()) + 1;
    }
    if (i_req_output < 2 * TOP && i_req_output >= 0 &&
        !output_knn.write_addr.full() && !output_knn.write_data.full()) {
      outval = *(INT32 *)&cur_id;
      output_knn.write_addr.write(i_req_output * sizeof(INT32));
      output_knn.write_data.write(outval);
      --i_req_output;
    }
    if (!output_knn.write_resp.empty()) {
      i_resp_output += (unsigned int)(output_knn.write_resp.read()) + 1;
    }
  }
}