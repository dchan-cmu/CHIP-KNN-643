#include "knn.h"
#define printf(...) ((void)0)
#define absval(input)                                                          \
  ((input) > 0 ? static_cast<DATA_TYPE>(input)                                 \
               : static_cast<DATA_TYPE>(-1 * (input)))

void load_KNN(int debug_PE_ID, tapa::async_mmap<INTERFACE_WIDTH> &searchSpace,
              tapa::ostream<INTERFACE_WIDTH> &load_to_compute_stream) {
#pragma HLS interface ap_fifo port = load_to_compute_stream
#pragma HLS interface ap_fifo port = searchSpace.read_addr
#pragma HLS interface ap_fifo port = searchSpace.read_data
#pragma HLS interface ap_fifo port = searchSpace.write_addr
#pragma HLS interface ap_fifo port = searchSpace.write_data
#pragma HLS interface ap_fifo port = searchSpace.write_resp
#pragma HLS disaggregate variable = searchSpace

#pragma HLS INLINE OFF
  INTERFACE_WIDTH loaded_value = 0;

LOAD_QUERY:
  for (int i_req = 0, i_resp = 0;
       i_resp < (INPUT_DIM - 1) / NUM_FEATURES_PER_READ + 1;) {
#pragma HLS loop_tripcount min = ((INPUT_DIM - 1) / NUM_FEATURES_PER_READ + 1) \
    max = ((INPUT_DIM - 1) / NUM_FEATURES_PER_READ + 1)
#pragma HLS pipeline II = 1
    // Think of addr as an array index.
    int addr = i_req;
    if (i_req < (INPUT_DIM - 1) / NUM_FEATURES_PER_READ + 1 &&
        !searchSpace.read_addr.full()) {
      searchSpace.read_addr.write(addr * sizeof(INTERFACE_WIDTH));
      i_req++;
    }

    if (!searchSpace.read_data.empty()) {
      loaded_value = searchSpace.read_data.read();
      i_resp++;

// DEBUGGING:
#ifndef __SYNTHESIS__
      for (int i = 0; i < NUM_FEATURES_PER_READ; ++i) {
        DATA_TYPE cur_value = 0;
        DATA_TYPE tmp;
        tmp.range(DATA_TYPE_TOTAL_SZ - 1, 0) =
            loaded_value(i * DATA_TYPE_TOTAL_SZ + (DATA_TYPE_TOTAL_SZ - 1),
                         i * DATA_TYPE_TOTAL_SZ);

        cur_value = *((DATA_TYPE *)(&tmp));
        if (cur_value < MAX_DATA_TYPE_VAL && debug_PE_ID == 0) {
          printf("LOAD QUERY: value = %f, i_resp = %d\n", cur_value.to_float(),
                 i_resp);
        }
      }
#endif

      load_to_compute_stream.write(loaded_value);
    }
  }

LOAD_SEARCHSPACE:
  for (int i_req = 0, i_resp = 0; i_resp < PARTITION_LEN_IN_I;) {
#pragma HLS loop_tripcount min = PARTITION_LEN_IN_I max = PARTITION_LEN_IN_I
#pragma HLS pipeline II = 1
    // Think of addr as an array index.
    int addr = QUERY_DATA_RESERVE + i_req;
    if (i_req < PARTITION_LEN_IN_I && !searchSpace.read_addr.full()) {
      searchSpace.read_addr.write(addr * sizeof(INTERFACE_WIDTH));
      i_req++;
    }
    if (!searchSpace.read_data.empty()) {
      loaded_value = searchSpace.read_data.read();
      i_resp++;

      //// DEBUGGING: Printing the loaded data:
      // #ifndef __SYNTHESIS__
      // for (int i = 0; i < NUM_FEATURES_PER_READ; ++i)
      //{
      //     DATA_TYPE cur_value = 0;
      //     TRANSFER_TYPE tmp;
      //     tmp.range(DATA_TYPE_TOTAL_SZ - 1, 0)
      //         = loaded_value(i*DATA_TYPE_TOTAL_SZ + (DATA_TYPE_TOTAL_SZ - 1),
      //                         i*DATA_TYPE_TOTAL_SZ);
      //     cur_value = *((DATA_TYPE*) (&tmp));
      //     if (cur_value < MAX_DATA_TYPE_VAL && debug_PE_ID == 0)
      //     {
      //         printf("LOAD SEARCHSPACE: value = %f, i_resp = %d\n",
      //         cur_value, i_resp);
      //     }
      // }
      // #endif

      //// DEBUGGING: Printing how many times we write to each stream:
      // #ifndef __SYNTHESIS__
      // if (debug_PE_ID == 0)
      //{
      //     printf("LOAD: Writing to load_to_compute_stream for the %d-th
      //     time\n",
      //             i_resp-1);
      // }
      // #endif

      load_to_compute_stream.write(loaded_value);
    }
  }
}