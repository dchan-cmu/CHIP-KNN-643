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

#define KNN_SWAP(a, b, x, y)                                                   \
  do {                                                                         \
    DATA_TYPE _tmpdist_a = *(a);                                               \
    DATA_TYPE _tmpdist_b = *(b);                                               \
    *(b) = _tmpdist_a;                                                         \
    *(a) = _tmpdist_b;                                                         \
    int _tmpid_x = *(x);                                                       \
    int _tmpid_y = *(y);                                                       \
    *(x) = _tmpid_y;                                                           \
    *(y) = _tmpid_x;                                                           \
  } while (0)

void para_partial_sort(const int PE_idx,
                       tapa::istream<DATA_TYPE> &compute_to_sort_stream,
                       tapa::ostream<DATA_TYPE> &sort_to_hiermerge_dist_stream,
                       tapa::ostream<int> &sort_to_hiermerge_id_stream) {
#pragma HLS INLINE OFF

#ifndef __SYNTHESIS__
  printf("SORT UNIT FOR PE #%d IS STARTING NOW.\n", PE_idx);
#endif

#ifdef __SYNTHESIS__
  static // TAPA Known-issue: Static keyword fails CSIM because this is not
         // thread-safe.
         //  but when running the HW build, it will instantiate several copies
         //  of this function. So this is OK.
#endif
      DATA_TYPE local_kNearstDist[(TOP + 1)];
#pragma HLS ARRAY_PARTITION variable = local_kNearstDist complete dim = 0

#ifdef __SYNTHESIS__
  static
#endif
      int local_kNearstId[(TOP + 1)];
#pragma HLS ARRAY_PARTITION variable = local_kNearstId complete dim = 0

#ifndef __SYNTHESIS__
  int DEBUG_stream_counters = 0;
#endif

  int start_id = PE_idx * NUM_SP_PTS_PER_KRNL_PADDED;

/*******************************************/

// Initialize all top-K distances to MAX, and their IDs to an invalid value.
INIT_LOOP:
  for (int j = 0; j < TOP + 1; ++j) {
    local_kNearstId[j] = -1;
    local_kNearstDist[j] = MAX_DATA_TYPE_VAL;
  }

SORT_LOOP:
  for (int dvalue_idx = 0; dvalue_idx < (PARTITION_LEN_IN_D + TOP);
       ++dvalue_idx) {
#pragma HLS PIPELINE II = I2D_FACTOR_W
    DATA_TYPE cur_Dval = 0;

    if (dvalue_idx >= PARTITION_LEN_IN_D) {
      cur_Dval = MAX_DATA_TYPE_VAL;
    } else {
      // #ifndef __SYNTHESIS__
      // printf("PPS Unit for PE %d: Reading from compute_to_sort_stream, for
      // the %d-th time\n",
      //         PE_idx,
      //         DEBUG_stream_counters++);
      // #endif

      cur_Dval = compute_to_sort_stream.read();
    }

    local_kNearstDist[0] = cur_Dval;

    local_kNearstId[0] = start_id + dvalue_idx;

    // #ifndef __SYNTHESIS__
    // printf("SORT: Current ID = %d, cur_Dval = %f\n", start_id + dvalue_idx,
    // cur_Dval); printf("SORT: Best ID = %d, Best Dval = %f\n",
    // local_kNearstId[TOP], local_kNearstDist[TOP]); #endif

    // compare and swap odd
    for (int ii = 1; ii < TOP; ii += 2) {
#pragma HLS UNROLL
#pragma HLS DEPENDENCE variable = local_kNearstDist inter false
#pragma HLS DEPENDENCE variable = local_kNearstId inter false

      if (local_kNearstDist[ii] < local_kNearstDist[ii + 1]) {
        KNN_SWAP(&local_kNearstDist[ii], &local_kNearstDist[ii + 1],
                 &local_kNearstId[ii], &local_kNearstId[ii + 1]);
      }
    }

    // compare and swap even
    for (int ii = 1; ii < TOP + 1; ii += 2) {
#pragma HLS UNROLL
#pragma HLS DEPENDENCE variable = local_kNearstDist inter false
#pragma HLS DEPENDENCE variable = local_kNearstId inter false

      if (local_kNearstDist[ii] > local_kNearstDist[ii - 1]) {
        KNN_SWAP(&local_kNearstDist[ii], &local_kNearstDist[ii - 1],
                 &local_kNearstId[ii], &local_kNearstId[ii - 1]);
      }
    }
  }

// Write data out
OUTPUT_LOOP:
  for (int j = TOP; j > 0; --j) {
#pragma HLS PIPELINE II = 1
    sort_to_hiermerge_dist_stream.write(local_kNearstDist[j]);
    sort_to_hiermerge_id_stream.write(local_kNearstId[j]);
  }

#ifndef __SYNTHESIS__
  for (int j = 0; j < TOP + 1; ++j) {
    printf("AFTER SORT: local_kNearst[%3d]:\n", j);
    printf("AFTER SORT:     Dist = %5.10f\n", local_kNearstDist[j].to_float());
    printf("AFTER SORT:     Id = %d\n", local_kNearstId[j]);
  }
#endif

REINITIALIZATION_LOOP:
  for (int j = 0; j < TOP + 1; ++j) {
#pragma HLS UNROLL
    // Reset the kNearst values so we can run the next iteration.
    local_kNearstId[j] = -1;
    local_kNearstDist[j] = MAX_DATA_TYPE_VAL;
  }
}