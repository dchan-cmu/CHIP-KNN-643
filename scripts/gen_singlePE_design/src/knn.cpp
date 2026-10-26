#include "knn.h"
#define printf(...) ((void)0)
#define absval(input) ((input) > 0 ? static_cast<DATA_TYPE>(input) : static_cast<DATA_TYPE>(-1 * (input)))

#define SORT_TO_HIERMERGE_STREAM_ARGS(PE) \
    L0_out_dist_##PE,  \
    L0_out_id_##PE



#define INVOKE_PPS_UNITS_FOR_PE(PE) \
    .invoke(para_partial_sort, PE, compute_to_sort_stream_##PE, SORT_TO_HIERMERGE_STREAM_ARGS(PE) ) \


/*************************************************/
/******************** LOADS: *********************/
/*************************************************/
void load_KNN(   int debug_PE_ID,
                 tapa::async_mmap<INTERFACE_WIDTH> & searchSpace,
                 tapa::ostream<INTERFACE_WIDTH>& load_to_compute_stream)
{
#pragma HLS INLINE OFF
    INTERFACE_WIDTH loaded_value = 0;


    LOAD_QUERY: 
    for (int i_req = 0, i_resp = 0; i_resp < (INPUT_DIM-1)/NUM_FEATURES_PER_READ + 1; ) {
        #pragma HLS loop_tripcount min=((INPUT_DIM-1)/NUM_FEATURES_PER_READ + 1) max=((INPUT_DIM-1)/NUM_FEATURES_PER_READ + 1)
        #pragma HLS pipeline II=1
        //Think of addr as an array index.
        int addr = i_req;
        if (i_req < (INPUT_DIM-1)/NUM_FEATURES_PER_READ + 1 && !searchSpace.read_addr.full()) {
            searchSpace.read_addr.write(addr * sizeof(INTERFACE_WIDTH));
            i_req++;
        }

        if (!searchSpace.read_data.empty()) {
            loaded_value = searchSpace.read_data.read();
            i_resp++;

            // DEBUGGING:
            #ifndef __SYNTHESIS__
            for (int i = 0; i < NUM_FEATURES_PER_READ; ++i)
            {
                DATA_TYPE cur_value = 0;
                DATA_TYPE tmp;
                tmp.range(DATA_TYPE_TOTAL_SZ - 1, 0)
                    = loaded_value(i*DATA_TYPE_TOTAL_SZ + (DATA_TYPE_TOTAL_SZ - 1),
                                    i*DATA_TYPE_TOTAL_SZ);

                cur_value = *((DATA_TYPE*) (&tmp));
                if (cur_value < MAX_DATA_TYPE_VAL && debug_PE_ID == 0)
                {
                    printf("LOAD QUERY: value = %f, i_resp = %d\n", cur_value.to_float(), i_resp);
                }
            }
            #endif


            load_to_compute_stream.write(loaded_value);
        }
    }

    LOAD_SEARCHSPACE:
    for (int i_req = 0, i_resp = 0; i_resp < PARTITION_LEN_IN_I; ) {
        #pragma HLS loop_tripcount min=PARTITION_LEN_IN_I max=PARTITION_LEN_IN_I
        #pragma HLS pipeline II=1
        //Think of addr as an array index.
        int addr = QUERY_DATA_RESERVE + i_req;
        if (i_req < PARTITION_LEN_IN_I && !searchSpace.read_addr.full()) {
            searchSpace.read_addr.write(addr * sizeof(INTERFACE_WIDTH));
            i_req++;
        }
        if (!searchSpace.read_data.empty()) {
            loaded_value = searchSpace.read_data.read();
            i_resp++;

            //// DEBUGGING: Printing the loaded data:
            //#ifndef __SYNTHESIS__
            //for (int i = 0; i < NUM_FEATURES_PER_READ; ++i)
            //{
            //    DATA_TYPE cur_value = 0;
            //    TRANSFER_TYPE tmp;
            //    tmp.range(DATA_TYPE_TOTAL_SZ - 1, 0)
            //        = loaded_value(i*DATA_TYPE_TOTAL_SZ + (DATA_TYPE_TOTAL_SZ - 1),
            //                        i*DATA_TYPE_TOTAL_SZ);
            //    cur_value = *((DATA_TYPE*) (&tmp));
            //    if (cur_value < MAX_DATA_TYPE_VAL && debug_PE_ID == 0)
            //    {
            //        printf("LOAD SEARCHSPACE: value = %f, i_resp = %d\n", cur_value, i_resp);
            //    }
            //}
            //#endif

            //// DEBUGGING: Printing how many times we write to each stream:
            //#ifndef __SYNTHESIS__
            //if (debug_PE_ID == 0)
            //{
            //    printf("LOAD: Writing to load_to_compute_stream for the %d-th time\n",
            //            i_resp-1);
            //}
            //#endif

            load_to_compute_stream.write(loaded_value);
        }
    }
}
/*************************************************/
/******************* COMPUTES: *******************/
/*************************************************/

void compute_KNN(   int debug_pe_idx,
                    int debug_start_idx,
                    tapa::istream<INTERFACE_WIDTH>&     load_to_compute_stream,
                    tapa::ostream<DATA_TYPE>&     compute_to_sort_stream)
{
#pragma HLS INLINE OFF

    #ifndef __SYNTHESIS__
    int DEBUG_load_ctr = 0;
    #endif

    INTERFACE_WIDTH cur_data = 0;
    DATA_TYPE local_Query[INPUT_DIM];
    #pragma HLS ARRAY_PARTITION variable=local_Query complete dim=1

    #ifndef __SYNTHESIS__
    int DEBUG_write_counters = {};
    #endif

    /***********************************************/

    GET_QUERYDATA:
    for (int i = 0 ; i < CEIL_DIVISION(INPUT_DIM, NUM_FEATURES_PER_READ); ++i)
    {
        DATA_TYPE tmp = 0;
        int input_dim_idx = i*NUM_FEATURES_PER_READ;

        cur_data = load_to_compute_stream.read();

        for ( int j = 0; 
              j < NUM_FEATURES_PER_READ && input_dim_idx < INPUT_DIM; 
              ++j, ++input_dim_idx) 
        {
            tmp.range(DATA_TYPE_TOTAL_SZ-1, 0)
                = cur_data.range(j*DATA_TYPE_TOTAL_SZ + (DATA_TYPE_TOTAL_SZ-1),
                                 j*DATA_TYPE_TOTAL_SZ);

            local_Query[input_dim_idx] = tmp;
        }
    }

    COMPUTE_DATA:
    for (int ii = 0; ii < PARTITION_LEN_IN_D; ++ii){
        DATA_TYPE dist_val_outer = 0;

        for (int jj = 0 ; jj < I2D_FACTOR_W; ++jj){
        #pragma HLS PIPELINE II=1
            cur_data = load_to_compute_stream.read();
            DATA_TYPE dist_val_inner = 0;

            for (int kk = 0; kk < NUM_FEATURES_PER_READ; ++kk) {
                #pragma HLS UNROLL
                int range_idx = kk*DATA_TYPE_TOTAL_SZ;
                int querypt_idx = jj*NUM_FEATURES_PER_READ + kk;

                DATA_TYPE sp_dim_item_value;
                sp_dim_item_value.range(DATA_TYPE_TOTAL_SZ-1, 0) =
                    cur_data.range(range_idx + (DATA_TYPE_TOTAL_SZ-1),
                                   range_idx);

                #if DISTANCE_METRIC == 0        // Manhattan
                DATA_TYPE delta = absval(sp_dim_item_value - local_Query[querypt_idx]);
                dist_val_inner += delta;
                #elif DISTANCE_METRIC == 1 // L2
                DATA_TYPE delta = absval(sp_dim_item_value - local_Query[querypt_idx]);
                dist_val_inner += delta * delta;
                #endif
            }

            dist_val_outer += dist_val_inner;
        }

        //#ifndef __SYNTHESIS__
        //if (dist_val_outer < MAX_DATA_TYPE_VAL && ii % 1000 == 0){
        //    printf("KDEBUG: In compute, the %d-th computed value has dist_val_outer = %f\n", 
        //            ii, dist_val_outer.to_float());
        //}
        //#endif

        compute_to_sort_stream.write(dist_val_outer);
    }
}
#define KNN_SWAP(a, b, x, y) do { \
    DATA_TYPE _tmpdist_a = *(a); \
    DATA_TYPE _tmpdist_b = *(b); \
    *(b) = _tmpdist_a; \
    *(a) = _tmpdist_b; \
    int _tmpid_x = *(x); \
    int _tmpid_y = *(y); \
    *(x) = _tmpid_y; \
    *(y) = _tmpid_x; \
} while(0)

void para_partial_sort(const int PE_idx,
                       tapa::istream<DATA_TYPE>&     compute_to_sort_stream,
                       tapa::ostream<DATA_TYPE>&     sort_to_hiermerge_dist_stream,
                       tapa::ostream<int>&           sort_to_hiermerge_id_stream)
{
#pragma HLS INLINE OFF

    #ifndef __SYNTHESIS__
    printf("SORT UNIT FOR PE #%d IS STARTING NOW.\n", PE_idx);
    #endif

    #ifdef __SYNTHESIS__
    static      // TAPA Known-issue: Static keyword fails CSIM because this is not thread-safe. 
                //  but when running the HW build, it will instantiate several copies of this function. So this is OK.
    #endif
    DATA_TYPE local_kNearstDist[(TOP+1)];
    #pragma HLS ARRAY_PARTITION variable=local_kNearstDist complete dim=0

    #ifdef __SYNTHESIS__
    static
    #endif
    int local_kNearstId[(TOP+1)];
    #pragma HLS ARRAY_PARTITION variable=local_kNearstId complete dim=0

    #ifndef __SYNTHESIS__
    int DEBUG_stream_counters = 0;
    #endif

    int start_id = PE_idx * NUM_SP_PTS_PER_KRNL_PADDED;

    /*******************************************/

    // Initialize all top-K distances to MAX, and their IDs to an invalid value.
    INIT_LOOP:
    for (int j = 0; j < TOP+1; ++j)
    {
        local_kNearstId[j] = -1;
        local_kNearstDist[j] = MAX_DATA_TYPE_VAL;
    }

    SORT_LOOP:
    for (int dvalue_idx = 0; dvalue_idx < (PARTITION_LEN_IN_D + TOP); ++dvalue_idx) {
    #pragma HLS PIPELINE II=I2D_FACTOR_W
        DATA_TYPE cur_Dval = 0;

        if (dvalue_idx >= PARTITION_LEN_IN_D) {
            cur_Dval = MAX_DATA_TYPE_VAL;
        } else {
            //#ifndef __SYNTHESIS__
            //printf("PPS Unit for PE %d: Reading from compute_to_sort_stream, for the %d-th time\n", 
            //        PE_idx,
            //        DEBUG_stream_counters++);
            //#endif

            cur_Dval = compute_to_sort_stream.read();
        }

        local_kNearstDist[0] = cur_Dval;

        local_kNearstId[0] = start_id + dvalue_idx;

        //#ifndef __SYNTHESIS__
        //printf("SORT: Current ID = %d, cur_Dval = %f\n", start_id + dvalue_idx, cur_Dval);
        //printf("SORT: Best ID = %d, Best Dval = %f\n", local_kNearstId[TOP], local_kNearstDist[TOP]);
        //#endif


        //compare and swap odd
        for(int ii=1; ii<TOP; ii+=2){
        #pragma HLS UNROLL
        #pragma HLS DEPENDENCE variable=local_kNearstDist inter false
        #pragma HLS DEPENDENCE variable=local_kNearstId inter false

            if (local_kNearstDist[ii] < local_kNearstDist[ii+1]){
                KNN_SWAP(&local_kNearstDist[ii], &local_kNearstDist[ii+1], 
                          &local_kNearstId[ii], &local_kNearstId[ii+1]);
            }

        }


        //compare and swap even
        for(int ii=1; ii<TOP+1; ii+=2){
        #pragma HLS UNROLL
        #pragma HLS DEPENDENCE variable=local_kNearstDist inter false
        #pragma HLS DEPENDENCE variable=local_kNearstId inter false

            if (local_kNearstDist[ii] > local_kNearstDist[ii-1]){
                KNN_SWAP(&local_kNearstDist[ii], &local_kNearstDist[ii-1], 
                          &local_kNearstId[ii], &local_kNearstId[ii-1]);
            }

        }
    }

    // Write data out
    OUTPUT_LOOP:
    for (int j = TOP; j > 0; --j)
    {
    #pragma HLS PIPELINE II=1
        sort_to_hiermerge_dist_stream.write(local_kNearstDist[j]);
        sort_to_hiermerge_id_stream.write(local_kNearstId[j]);
    }

    #ifndef __SYNTHESIS__
    for (int j = 0; j < TOP+1; ++j)
    {
        printf("AFTER SORT: local_kNearst[%3d]:\n", j);
        printf("AFTER SORT:     Dist = %5.10f\n",   local_kNearstDist[j].to_float());
        printf("AFTER SORT:     Id = %d\n",         local_kNearstId[j]);

    }
    #endif

    REINITIALIZATION_LOOP:
    for (int j = 0; j < TOP+1; ++j){
    #pragma HLS UNROLL
        // Reset the kNearst values so we can run the next iteration.
        local_kNearstId[j] = -1;
        local_kNearstDist[j] = MAX_DATA_TYPE_VAL;
    }
}




void krnl_singlePE_Write_Outputs(
    tapa::istream<DATA_TYPE> &in_dist0,
    tapa::istream<int> &in_id0,
    tapa::async_mmap<INT32>& output_knn
) {
    DATA_TYPE cur_dist;
    int cur_id;
    int i_req_output = 2*TOP-1; 
    int i_resp_output = 2*TOP-1;
    for (int i = 0; i < TOP; ++i ) {
        #pragma HLS pipeline II=1
        cur_dist = in_dist0.read();
        cur_id = in_id0.read();
        INT32 outval = 0;
        if (i_req_output < 2*TOP && i_req_output >= 0 && !output_knn.write_addr.full() && !output_knn.write_data.full()) {
            outval.range(DATA_TYPE_TOTAL_SZ-1, 0) = cur_dist.range(DATA_TYPE_TOTAL_SZ-1, 0);
            output_knn.write_addr.write(i_req_output * sizeof(INT32));
            output_knn.write_data.write(outval);
            --i_req_output;
        }
        if (!output_knn.write_resp.empty()) {
            i_resp_output += (unsigned int) (output_knn.write_resp.read()) + 1;
        }
        if (i_req_output < 2*TOP && i_req_output >= 0 && !output_knn.write_addr.full() && !output_knn.write_data.full()) {
            outval = * (INT32*) &cur_id;
            output_knn.write_addr.write(i_req_output * sizeof(INT32));
            output_knn.write_data.write(outval);
            --i_req_output;
        }
        if (!output_knn.write_resp.empty()) {
            i_resp_output += (unsigned int) (output_knn.write_resp.read()) + 1;
        }
    }
}


void Knn(
    tapa::mmap<INTERFACE_WIDTH> in_0,
    tapa::mmap<INT32> final_out
) {

    // Streams, for the global merge:
    tapa::stream<DATA_TYPE, TOP> L0_out_dist_0;
    tapa::stream<int,       TOP> L0_out_id_0;
    // Streams, for load->compute->sort:
    tapa::stream<INTERFACE_WIDTH, 2>           load_to_compute_stream_0;
    tapa::stream<DATA_TYPE, 2>           compute_to_sort_stream_0;


    tapa::task()
        .invoke( load_KNN, 0, in_0, load_to_compute_stream_0)

        .invoke( compute_KNN, 0, NUM_SP_PTS_PER_KRNL_PADDED*0, load_to_compute_stream_0, compute_to_sort_stream_0  )

        INVOKE_PPS_UNITS_FOR_PE(0)

        ////////// MERGING LOGIC



        // INTER-PE HIERMERGE:
        .invoke( krnl_singlePE_Write_Outputs,  L0_out_dist_0,  L0_out_id_0,
                                               final_out);
}
