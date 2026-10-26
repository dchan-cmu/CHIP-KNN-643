#include "knn.h"
#define printf(...) ((void)0)
#define absval(input)                                                          \
  ((input) > 0 ? static_cast<DATA_TYPE>(input)                                 \
               : static_cast<DATA_TYPE>(-1 * (input)))

void krnl_singlePE_Write_Outputs(tapa::istream<DATA_TYPE> &in_dist0,
                                 tapa::istream<int> &in_id0,
                                 tapa::async_mmap<INT32> &output_knn) {
#pragma HLS interface ap_fifo port = in_dist0
#pragma HLS interface ap_fifo port = in_id0
#pragma HLS interface ap_fifo port = output_knn.read_addr
#pragma HLS interface ap_fifo port = output_knn.read_data
#pragma HLS interface ap_fifo port = output_knn.write_addr
#pragma HLS interface ap_fifo port = output_knn.write_data
#pragma HLS interface ap_fifo port = output_knn.write_resp
#pragma HLS disaggregate variable = output_knn

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