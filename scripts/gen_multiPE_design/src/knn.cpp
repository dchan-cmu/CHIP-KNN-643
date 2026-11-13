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
    DATA_TYPE _tmpdist = (a); \
    (a) = (b); \
    (b) = _tmpdist; \
    int _tmpid = (x); \
    (x) = (y); \
    (y) = _tmpid; \
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
                KNN_SWAP(local_kNearstDist[ii], local_kNearstDist[ii+1], 
                         local_kNearstId[ii], local_kNearstId[ii+1]);
            }

        }


        //compare and swap even
        for(int ii=1; ii<TOP+1; ii+=2){
        #pragma HLS UNROLL
        #pragma HLS DEPENDENCE variable=local_kNearstDist inter false
        #pragma HLS DEPENDENCE variable=local_kNearstId inter false

            if (local_kNearstDist[ii] > local_kNearstDist[ii-1]){
                KNN_SWAP(local_kNearstDist[ii], local_kNearstDist[ii-1], 
                         local_kNearstId[ii], local_kNearstId[ii-1]);
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





void write_out_mmap(
                    tapa::async_mmap<INT32>&    output_knn,
                    DATA_TYPE                   output_dist,
                    int                         output_id,
                    int&                        i_req_output, 
                    int&                        i_resp_output
) {
#pragma HLS INLINE
    INT32 outval = 0;

    if (i_req_output < 2*TOP && i_req_output >= 0 && 
        !output_knn.write_addr.full() && 
        !output_knn.write_data.full()
    ) {
        outval.range(DATA_TYPE_TOTAL_SZ-1, 0) = output_dist.range(DATA_TYPE_TOTAL_SZ-1, 0);

        //#ifndef __SYNTHESIS__
        //printf("KDEBUG: i_req_output = %d. Outval = %f, output_dist = %f.\n",
        //        i_req_output, outval.to_float(), output_dist.to_float());
        //#endif

        output_knn.write_addr.write(i_req_output * sizeof(INT32));
        output_knn.write_data.write(outval);
        --i_req_output;
    }

    if (!output_knn.write_resp.empty()) {
        i_resp_output += (unsigned int) (output_knn.write_resp.read()) + 1;
    }

    if (i_req_output < 2*TOP && i_req_output >= 0 && 
        !output_knn.write_addr.full() && 
        !output_knn.write_data.full()
    ) {
        outval = * (INT32*) &output_id;

        //#ifndef __SYNTHESIS__
        //printf("KDEBUG: i_req_output = %d. Outval = %f, output_id = %d\n",
        //        i_req_output, outval.to_float(), output_id);
        //#endif

        output_knn.write_addr.write(i_req_output * sizeof(INT32));
        output_knn.write_data.write(outval);
        --i_req_output;
    }

    if (!output_knn.write_resp.empty()) {
        i_resp_output += (unsigned int) (output_knn.write_resp.read()) + 1;
    }
}


void merge_dual_streams(
                        int debug_PE_idx,
                        int debug_seg_d2l_idx,
                        int debug_stage_idx,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_1,
                        tapa::istream<int>&         hiermerge_id_istream_1,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_2,
                        tapa::istream<int>&         hiermerge_id_istream_2,
                        tapa::ostream<DATA_TYPE>&   hiermerge_dist_ostream,
                        tapa::ostream<int>&         hiermerge_id_ostream
)
{

    #ifndef __SYNTHESIS__
    printf("NOTE: USING MONOMERGE!\n");
    #endif

    DATA_TYPE dist_1 = hiermerge_dist_istream_1.read();
    DATA_TYPE dist_2 = hiermerge_dist_istream_2.read();
    int id_1 = hiermerge_id_istream_1.read();
    int id_2 = hiermerge_id_istream_2.read();
    int stream1_read_count = 1;
    int stream2_read_count = 1;

    for (int k = TOP-1; k > 0; --k)
    {
        #ifndef __SYNTHESIS__
        if (debug_PE_idx == 0)
        {
            printf("KDEBUG: Hiermerge for PE %d, STAGE %d, seg_d2l = %d, stream1_read_count = %d, stream2_read_count = %d\n", 
                    debug_PE_idx, debug_stage_idx, debug_seg_d2l_idx,
                    stream1_read_count, stream2_read_count);
        }
        #endif
        if (dist_1 <= dist_2)
        {
            hiermerge_dist_ostream.write(dist_1);
            hiermerge_id_ostream.write(id_1);

            if (stream1_read_count < TOP)
            {
                ++stream1_read_count;
                dist_1 = hiermerge_dist_istream_1.read();
                id_1 = hiermerge_id_istream_1.read();
            }
        }
        else
        {
            hiermerge_dist_ostream.write(dist_2);
            hiermerge_id_ostream.write(id_2);

            if (stream2_read_count < TOP)
            {
                ++stream2_read_count;
                dist_2 = hiermerge_dist_istream_2.read();
                id_2 = hiermerge_id_istream_2.read();
            }
        }
    }
    // Final write.
    if (dist_1 <= dist_2) {
        hiermerge_dist_ostream.write(dist_1);
        hiermerge_id_ostream.write(id_1);
    }
    else {
        hiermerge_dist_ostream.write(dist_2);
        hiermerge_id_ostream.write(id_2);
    }

    #ifndef __SYNTHESIS__
    if (debug_PE_idx == 0)
    {
        printf("KDEBUG: Hiermerge for PE %d, STAGE #%d, seg_d2l = %d, Emptying the input FIFOs now...\n",
                debug_PE_idx, debug_stage_idx, debug_seg_d2l_idx);
    }
    #endif
    // Empty the input streams.
    // NOTE: The total tripcount of these loops will be TOP.
    while (stream1_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP/2 max=TOP/2
        ++stream1_read_count;
        dist_1 = hiermerge_dist_istream_1.read();
        id_1 = hiermerge_id_istream_1.read();
    }
    while (stream2_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP/2 max=TOP/2
        ++stream2_read_count;
        dist_2 = hiermerge_dist_istream_2.read();
        id_2 = hiermerge_id_istream_2.read();
    }
}


void merge_trio_streams(
                        int debug_PE_idx,
                        int debug_seg_d2l_idx,
                        int debug_stage_idx,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_1,
                        tapa::istream<int>&         hiermerge_id_istream_1,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_2,
                        tapa::istream<int>&         hiermerge_id_istream_2,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_3,
                        tapa::istream<int>&         hiermerge_id_istream_3,
                        tapa::ostream<DATA_TYPE>&   hiermerge_dist_ostream,
                        tapa::ostream<int>&         hiermerge_id_ostream
)
{
    DATA_TYPE dist_1 = hiermerge_dist_istream_1.read();
    DATA_TYPE dist_2 = hiermerge_dist_istream_2.read();
    DATA_TYPE dist_3 = hiermerge_dist_istream_3.read();
    int id_1 = hiermerge_id_istream_1.read();
    int id_2 = hiermerge_id_istream_2.read();
    int id_3 = hiermerge_id_istream_3.read();
    int stream1_read_count = 1;
    int stream2_read_count = 1;
    int stream3_read_count = 1;

    for (int k = TOP-1; k > 0; --k)
    {
        #ifndef __SYNTHESIS__
        if (debug_PE_idx == 0)
        {
            printf("KDEBUG: Hiermerge for PE %d, STAGE %d, seg_d2l = %d, stream1_read_count = %d, stream2_read_count = %d, stream3_read_count = %d\n", 
                    debug_PE_idx, debug_stage_idx, debug_seg_d2l_idx,
                    stream1_read_count, stream2_read_count, stream3_read_count);
        }
        #endif

        if ( (dist_1 <= dist_2) && (dist_1 <= dist_3) )
        {
            hiermerge_dist_ostream.write(dist_1);
            hiermerge_id_ostream.write(id_1);

            if (stream1_read_count < TOP)
            {
                ++stream1_read_count;
                dist_1 = hiermerge_dist_istream_1.read();
                id_1 = hiermerge_id_istream_1.read();
            }
        }

        else if ( (dist_2 <= dist_3) && (dist_2 <= dist_1) )
        {
            hiermerge_dist_ostream.write(dist_2);
            hiermerge_id_ostream.write(id_2);

            if (stream2_read_count < TOP)
            {
                ++stream2_read_count;
                dist_2 = hiermerge_dist_istream_2.read();
                id_2 = hiermerge_id_istream_2.read();
            }
        }
        else
        {
            hiermerge_dist_ostream.write(dist_3);
            hiermerge_id_ostream.write(id_3);

            if (stream3_read_count < TOP)
            {
                ++stream3_read_count;
                dist_3 = hiermerge_dist_istream_3.read();
                id_3 = hiermerge_id_istream_3.read();
            }
        }
    }
    // Final write.
    if ( (dist_1 <= dist_2) && (dist_1 <= dist_3) ){
        hiermerge_dist_ostream.write(dist_1);
        hiermerge_id_ostream.write(id_1);
    }
    else if ( (dist_2 <= dist_3) && (dist_2 <= dist_1) ){
        hiermerge_dist_ostream.write(dist_2);
        hiermerge_id_ostream.write(id_2);
    }
    else{
        hiermerge_dist_ostream.write(dist_3);
        hiermerge_id_ostream.write(id_3);
    }

    #ifndef __SYNTHESIS__
    if (debug_PE_idx == 0)
    {
        printf("KDEBUG: Hiermerge for PE %d, STAGE #%d, seg_d2l = %d, Emptying the input FIFOs now...\n",
                debug_PE_idx, debug_stage_idx, debug_seg_d2l_idx);
    }
    #endif
    // Empty the input streams.
    // NOTE: The total tripcount of these loops will be 2*TOP.
    while (stream1_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP/2 max=TOP/2
        ++stream1_read_count;
        dist_1 = hiermerge_dist_istream_1.read();
        id_1 = hiermerge_id_istream_1.read();
    }
    while (stream2_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP/2 max=TOP/2
        ++stream2_read_count;
        dist_2 = hiermerge_dist_istream_2.read();
        id_2 = hiermerge_id_istream_2.read();
    }
    while (stream3_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP max=TOP
        ++stream3_read_count;
        dist_3 = hiermerge_dist_istream_3.read();
        id_3 = hiermerge_id_istream_3.read();
    }
}


void merge_dual_streams_FINAL(
                        int debug_PE_idx,
                        int debug_seg_d2l_idx,
                        int debug_stage_idx,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_1,
                        tapa::istream<int>&         hiermerge_id_istream_1,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_2,
                        tapa::istream<int>&         hiermerge_id_istream_2,
                        tapa::async_mmap<INT32>&    hiermerge_output
)
{
    DATA_TYPE dist_1 = hiermerge_dist_istream_1.read();
    DATA_TYPE dist_2 = hiermerge_dist_istream_2.read();
    int id_1 = hiermerge_id_istream_1.read();
    int id_2 = hiermerge_id_istream_2.read();
    int stream1_read_count = 1;
    int stream2_read_count = 1;
    int i_req_output  = 2*TOP-1;
    int i_resp_output = 2*TOP-1;

    for (int k = TOP-1; k > 0; --k)
    {
        #ifndef __SYNTHESIS__
        if (debug_PE_idx == 0)
        {
            printf("KDEBUG: FINAL Hiermerge, stream1_read_count = %d, stream2_read_count = %d\n", 
                    stream1_read_count, stream2_read_count);
        }
        #endif
        if (dist_1 <= dist_2)
        {
            write_out_mmap( hiermerge_output,
                            dist_1,
                            id_1,
                            i_req_output, 
                            i_resp_output);

            if (stream1_read_count < TOP)
            {
                ++stream1_read_count;
                dist_1 = hiermerge_dist_istream_1.read();
                id_1 = hiermerge_id_istream_1.read();
            }
        }
        else
        {
            write_out_mmap( hiermerge_output,
                            dist_2,
                            id_2,
                            i_req_output, 
                            i_resp_output);

            if (stream2_read_count < TOP)
            {
                ++stream2_read_count;
                dist_2 = hiermerge_dist_istream_2.read();
                id_2 = hiermerge_id_istream_2.read();
            }
        }
    }
    // Final write.
    if (dist_1 <= dist_2) {
            write_out_mmap( hiermerge_output,
                            dist_1,
                            id_1,
                            i_req_output, 
                            i_resp_output);
    }
    else {
            write_out_mmap( hiermerge_output,
                            dist_2,
                            id_2,
                            i_req_output, 
                            i_resp_output);
    }

    #ifndef __SYNTHESIS__
    if (debug_PE_idx == 0)
    {
        printf("KDEBUG: FINAL Hiermerge, Emptying the input FIFOs now...\n");
    }
    #endif
    // Empty the input streams.
    while (stream1_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP/2 max=TOP/2
        ++stream1_read_count;
        dist_1 = hiermerge_dist_istream_1.read();
        id_1 = hiermerge_id_istream_1.read();
    }
    while (stream2_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP/2 max=TOP/2
        ++stream2_read_count;
        dist_2 = hiermerge_dist_istream_2.read();
        id_2 = hiermerge_id_istream_2.read();
    }
}


void merge_trio_streams_FINAL(
                        int debug_PE_idx,
                        int debug_seg_d2l_idx,
                        int debug_stage_idx,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_1,
                        tapa::istream<int>&         hiermerge_id_istream_1,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_2,
                        tapa::istream<int>&         hiermerge_id_istream_2,
                        tapa::istream<DATA_TYPE>&   hiermerge_dist_istream_3,
                        tapa::istream<int>&         hiermerge_id_istream_3,
                        tapa::async_mmap<INT32>&    hiermerge_output
)
{
    DATA_TYPE dist_1 = hiermerge_dist_istream_1.read();
    DATA_TYPE dist_2 = hiermerge_dist_istream_2.read();
    DATA_TYPE dist_3 = hiermerge_dist_istream_3.read();
    int id_1 = hiermerge_id_istream_1.read();
    int id_2 = hiermerge_id_istream_2.read();
    int id_3 = hiermerge_id_istream_3.read();
    int stream1_read_count = 1;
    int stream2_read_count = 1;
    int stream3_read_count = 1;
    int i_req_output  = 2*TOP-1;
    int i_resp_output = 2*TOP-1;


    for (int k = TOP-1; k > 0; --k)
    {
        #ifndef __SYNTHESIS__
        if (debug_PE_idx == 0)
        {
            printf("KDEBUG: FINAL Hiermerge, stream1_read_count = %d, stream2_read_count = %d, stream3_read_count = %d\n", 
                    stream1_read_count, stream2_read_count, stream3_read_count);
        }
        #endif

        if ( (dist_1 <= dist_2) && (dist_1 <= dist_3) )
        {
            write_out_mmap( hiermerge_output,
                            dist_1,
                            id_1,
                            i_req_output, 
                            i_resp_output);

            if (stream1_read_count < TOP)
            {
                ++stream1_read_count;
                dist_1 = hiermerge_dist_istream_1.read();
                id_1 = hiermerge_id_istream_1.read();
            }
        }

        else if ( (dist_2 <= dist_3) && (dist_2 <= dist_1) )
        {
            write_out_mmap( hiermerge_output,
                            dist_2,
                            id_2,
                            i_req_output, 
                            i_resp_output);

            if (stream2_read_count < TOP)
            {
                ++stream2_read_count;
                dist_2 = hiermerge_dist_istream_2.read();
                id_2 = hiermerge_id_istream_2.read();
            }
        }
        else
        {
            write_out_mmap( hiermerge_output,
                            dist_3,
                            id_3,
                            i_req_output, 
                            i_resp_output);

            if (stream3_read_count < TOP)
            {
                ++stream3_read_count;
                dist_3 = hiermerge_dist_istream_3.read();
                id_3 = hiermerge_id_istream_3.read();
            }
        }
    }
    // Final write.
    if ( (dist_1 <= dist_2) && (dist_1 <= dist_3) ){
        write_out_mmap( hiermerge_output,
                        dist_1,
                        id_1,
                        i_req_output, 
                        i_resp_output);
    }
    else if ( (dist_2 <= dist_3) && (dist_2 <= dist_1) ){
        write_out_mmap( hiermerge_output,
                        dist_2,
                        id_2,
                        i_req_output, 
                        i_resp_output);
    }
    else{
        write_out_mmap( hiermerge_output,
                        dist_3,
                        id_3,
                        i_req_output, 
                        i_resp_output);
    }

    #ifndef __SYNTHESIS__
    if (debug_PE_idx == 0)
    {
        printf("KDEBUG: FINAL Hiermerge, Emptying the input FIFOs now...\n");
    }
    #endif
    // Empty the input streams.
    while (stream1_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP/2 max=TOP/2
        ++stream1_read_count;
        dist_1 = hiermerge_dist_istream_1.read();
        id_1 = hiermerge_id_istream_1.read();
    }
    while (stream2_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP/2 max=TOP/2
        ++stream2_read_count;
        dist_2 = hiermerge_dist_istream_2.read();
        id_2 = hiermerge_id_istream_2.read();
    }
    while (stream3_read_count < TOP)
    {
    #pragma HLS loop_tripcount min=TOP max=TOP
        ++stream3_read_count;
        dist_3 = hiermerge_dist_istream_3.read();
        id_3 = hiermerge_id_istream_3.read();
    }
}




void Knn(
    tapa::mmap<INTERFACE_WIDTH> in_0,
    tapa::mmap<INTERFACE_WIDTH> in_1,
    tapa::mmap<INTERFACE_WIDTH> in_2,
    tapa::mmap<INTERFACE_WIDTH> in_3,
    tapa::mmap<INT32> final_out
) {

    // Streams, for the global merge:
    tapa::stream<DATA_TYPE, TOP> L0_out_dist_0;
    tapa::stream<int,       TOP> L0_out_id_0;
    tapa::stream<DATA_TYPE, TOP> L0_out_dist_1;
    tapa::stream<int,       TOP> L0_out_id_1;
    tapa::stream<DATA_TYPE, TOP> L0_out_dist_2;
    tapa::stream<int,       TOP> L0_out_id_2;
    tapa::stream<DATA_TYPE, TOP> L0_out_dist_3;
    tapa::stream<int,       TOP> L0_out_id_3;
    tapa::stream<DATA_TYPE, 2> L1_out_dist_0;
    tapa::stream<int,       2> L1_out_id_0;
    tapa::stream<DATA_TYPE, 2> L1_out_dist_1;
    tapa::stream<int,       2> L1_out_id_1;
    // Streams, for load->compute->sort:
    tapa::stream<INTERFACE_WIDTH, 2>           load_to_compute_stream_0;
    tapa::stream<INTERFACE_WIDTH, 2>           load_to_compute_stream_1;
    tapa::stream<INTERFACE_WIDTH, 2>           load_to_compute_stream_2;
    tapa::stream<INTERFACE_WIDTH, 2>           load_to_compute_stream_3;
    tapa::stream<DATA_TYPE, 2>           compute_to_sort_stream_0;
    tapa::stream<DATA_TYPE, 2>           compute_to_sort_stream_1;
    tapa::stream<DATA_TYPE, 2>           compute_to_sort_stream_2;
    tapa::stream<DATA_TYPE, 2>           compute_to_sort_stream_3;


    tapa::task()
        .invoke( load_KNN, 0, in_0, load_to_compute_stream_0)
        .invoke( load_KNN, 1, in_1, load_to_compute_stream_1)
        .invoke( load_KNN, 2, in_2, load_to_compute_stream_2)
        .invoke( load_KNN, 3, in_3, load_to_compute_stream_3)

        .invoke( compute_KNN, 0, NUM_SP_PTS_PER_KRNL_PADDED*0, load_to_compute_stream_0, compute_to_sort_stream_0  )
        .invoke( compute_KNN, 1, NUM_SP_PTS_PER_KRNL_PADDED*1, load_to_compute_stream_1, compute_to_sort_stream_1  )
        .invoke( compute_KNN, 2, NUM_SP_PTS_PER_KRNL_PADDED*2, load_to_compute_stream_2, compute_to_sort_stream_2  )
        .invoke( compute_KNN, 3, NUM_SP_PTS_PER_KRNL_PADDED*3, load_to_compute_stream_3, compute_to_sort_stream_3  )

        INVOKE_PPS_UNITS_FOR_PE(0)
        INVOKE_PPS_UNITS_FOR_PE(1)
        INVOKE_PPS_UNITS_FOR_PE(2)
        INVOKE_PPS_UNITS_FOR_PE(3)

        ////////// MERGING LOGIC



        // INTER-PE HIERMERGE:

        .invoke( merge_dual_streams, -1, 0, -1, L0_out_dist_0, L0_out_id_0, L0_out_dist_1, L0_out_id_1, L1_out_dist_0, L1_out_id_0] )
        .invoke( merge_dual_streams, -1, 2, -1, L0_out_dist_2, L0_out_id_2, L0_out_dist_3, L0_out_id_3, L1_out_dist_1, L1_out_id_1] )

        .invoke( merge_dual_streams_FINAL, -1, 0, 0, L1_out_dist_0, L1_out_id_0, L1_out_dist_1, L1_out_id_1, final_out);
}
