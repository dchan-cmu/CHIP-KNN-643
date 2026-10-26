#include "knn.h"
#define printf(...) ((void)0)
#define absval(input)                                                          \
  ((input) > 0 ? static_cast<DATA_TYPE>(input)                                 \
               : static_cast<DATA_TYPE>(-1 * (input)))

void compute_KNN(int debug_pe_idx, int debug_start_idx,
                 tapa::istream<INTERFACE_WIDTH> &load_to_compute_stream,
                 tapa::ostream<DATA_TYPE> &compute_to_sort_stream) {
#pragma HLS interface ap_fifo port = load_to_compute_stream
#pragma HLS interface ap_fifo port = compute_to_sort_stream

#pragma HLS INLINE OFF

#ifndef __SYNTHESIS__
  int DEBUG_load_ctr = 0;
#endif

  INTERFACE_WIDTH cur_data = 0;
  DATA_TYPE local_Query[INPUT_DIM];
#pragma HLS ARRAY_PARTITION variable = local_Query complete dim = 1

#ifndef __SYNTHESIS__
  int DEBUG_write_counters = {};
#endif

  /***********************************************/

GET_QUERYDATA:
  for (int i = 0; i < CEIL_DIVISION(INPUT_DIM, NUM_FEATURES_PER_READ); ++i) {
    DATA_TYPE tmp = 0;
    int input_dim_idx = i * NUM_FEATURES_PER_READ;

    cur_data = load_to_compute_stream.read();

    for (int j = 0; j < NUM_FEATURES_PER_READ && input_dim_idx < INPUT_DIM;
         ++j, ++input_dim_idx) {
      tmp.range(DATA_TYPE_TOTAL_SZ - 1, 0) =
          cur_data.range(j * DATA_TYPE_TOTAL_SZ + (DATA_TYPE_TOTAL_SZ - 1),
                         j * DATA_TYPE_TOTAL_SZ);

      local_Query[input_dim_idx] = tmp;
    }
  }

COMPUTE_DATA:
  for (int ii = 0; ii < PARTITION_LEN_IN_D; ++ii) {
    DATA_TYPE dist_val_outer = 0;

    for (int jj = 0; jj < I2D_FACTOR_W; ++jj) {
#pragma HLS PIPELINE II = 1
      cur_data = load_to_compute_stream.read();
      DATA_TYPE dist_val_inner = 0;

      for (int kk = 0; kk < NUM_FEATURES_PER_READ; ++kk) {
#pragma HLS UNROLL
        int range_idx = kk * DATA_TYPE_TOTAL_SZ;
        int querypt_idx = jj * NUM_FEATURES_PER_READ + kk;

        DATA_TYPE sp_dim_item_value;
        sp_dim_item_value.range(DATA_TYPE_TOTAL_SZ - 1, 0) =
            cur_data.range(range_idx + (DATA_TYPE_TOTAL_SZ - 1), range_idx);

#if DISTANCE_METRIC == 0 // Manhattan
        DATA_TYPE delta = absval(sp_dim_item_value - local_Query[querypt_idx]);
        dist_val_inner += delta;
#elif DISTANCE_METRIC == 1 // L2
        DATA_TYPE delta = absval(sp_dim_item_value - local_Query[querypt_idx]);
        dist_val_inner += delta * delta;
#endif
      }

      dist_val_outer += dist_val_inner;
    }

    // #ifndef __SYNTHESIS__
    // if (dist_val_outer < MAX_DATA_TYPE_VAL && ii % 1000 == 0){
    //     printf("KDEBUG: In compute, the %d-th computed value has
    //     dist_val_outer = %f\n",
    //             ii, dist_val_outer.to_float());
    // }
    // #endif

    compute_to_sort_stream.write(dist_val_outer);
  }
}