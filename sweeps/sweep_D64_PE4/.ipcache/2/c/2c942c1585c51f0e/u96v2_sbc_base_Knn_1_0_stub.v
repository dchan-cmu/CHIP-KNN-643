// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2023.2 (lin64) Build 4029153 Fri Oct 13 20:13:54 MDT 2023
// Date        : Mon Nov 23 18:40:26 2026
// Host        : ece005.ece.local.cmu.edu running 64-bit Red Hat Enterprise Linux release 8.10 (Ootpa)
// Command     : write_verilog -force -mode synth_stub -rename_top decalper_eb_ot_sdeen_pot_pi_dehcac_xnilix -prefix
//               decalper_eb_ot_sdeen_pot_pi_dehcac_xnilix_ u96v2_sbc_base_Knn_1_0_stub.v
// Design      : u96v2_sbc_base_Knn_1_0
// Purpose     : Stub declaration of top-level module interface
// Device      : xczu3eg-sbva484-1-i
// --------------------------------------------------------------------------------

// This empty module with port declaration file causes synthesis tools to infer a black box for IP.
// The synthesis directives are for Synopsys Synplify support to prevent IO buffer insertion.
// Please paste the declaration into a Verilog source file or add the file as an additional source.
(* X_CORE_INFO = "Knn,Vivado 2023.2" *)
module decalper_eb_ot_sdeen_pot_pi_dehcac_xnilix(ap_clk, ap_rst_n, m_axi_gmem0_AWVALID, 
  m_axi_gmem0_AWREADY, m_axi_gmem0_AWADDR, m_axi_gmem0_AWID, m_axi_gmem0_AWLEN, 
  m_axi_gmem0_AWSIZE, m_axi_gmem0_AWBURST, m_axi_gmem0_AWLOCK, m_axi_gmem0_AWCACHE, 
  m_axi_gmem0_AWPROT, m_axi_gmem0_AWQOS, m_axi_gmem0_AWREGION, m_axi_gmem0_AWUSER, 
  m_axi_gmem0_WVALID, m_axi_gmem0_WREADY, m_axi_gmem0_WDATA, m_axi_gmem0_WSTRB, 
  m_axi_gmem0_WLAST, m_axi_gmem0_WID, m_axi_gmem0_WUSER, m_axi_gmem0_ARVALID, 
  m_axi_gmem0_ARREADY, m_axi_gmem0_ARADDR, m_axi_gmem0_ARID, m_axi_gmem0_ARLEN, 
  m_axi_gmem0_ARSIZE, m_axi_gmem0_ARBURST, m_axi_gmem0_ARLOCK, m_axi_gmem0_ARCACHE, 
  m_axi_gmem0_ARPROT, m_axi_gmem0_ARQOS, m_axi_gmem0_ARREGION, m_axi_gmem0_ARUSER, 
  m_axi_gmem0_RVALID, m_axi_gmem0_RREADY, m_axi_gmem0_RDATA, m_axi_gmem0_RLAST, 
  m_axi_gmem0_RID, m_axi_gmem0_RUSER, m_axi_gmem0_RRESP, m_axi_gmem0_BVALID, 
  m_axi_gmem0_BREADY, m_axi_gmem0_BRESP, m_axi_gmem0_BID, m_axi_gmem0_BUSER, 
  m_axi_gmem1_AWVALID, m_axi_gmem1_AWREADY, m_axi_gmem1_AWADDR, m_axi_gmem1_AWID, 
  m_axi_gmem1_AWLEN, m_axi_gmem1_AWSIZE, m_axi_gmem1_AWBURST, m_axi_gmem1_AWLOCK, 
  m_axi_gmem1_AWCACHE, m_axi_gmem1_AWPROT, m_axi_gmem1_AWQOS, m_axi_gmem1_AWREGION, 
  m_axi_gmem1_AWUSER, m_axi_gmem1_WVALID, m_axi_gmem1_WREADY, m_axi_gmem1_WDATA, 
  m_axi_gmem1_WSTRB, m_axi_gmem1_WLAST, m_axi_gmem1_WID, m_axi_gmem1_WUSER, 
  m_axi_gmem1_ARVALID, m_axi_gmem1_ARREADY, m_axi_gmem1_ARADDR, m_axi_gmem1_ARID, 
  m_axi_gmem1_ARLEN, m_axi_gmem1_ARSIZE, m_axi_gmem1_ARBURST, m_axi_gmem1_ARLOCK, 
  m_axi_gmem1_ARCACHE, m_axi_gmem1_ARPROT, m_axi_gmem1_ARQOS, m_axi_gmem1_ARREGION, 
  m_axi_gmem1_ARUSER, m_axi_gmem1_RVALID, m_axi_gmem1_RREADY, m_axi_gmem1_RDATA, 
  m_axi_gmem1_RLAST, m_axi_gmem1_RID, m_axi_gmem1_RUSER, m_axi_gmem1_RRESP, 
  m_axi_gmem1_BVALID, m_axi_gmem1_BREADY, m_axi_gmem1_BRESP, m_axi_gmem1_BID, 
  m_axi_gmem1_BUSER, m_axi_gmem2_AWVALID, m_axi_gmem2_AWREADY, m_axi_gmem2_AWADDR, 
  m_axi_gmem2_AWID, m_axi_gmem2_AWLEN, m_axi_gmem2_AWSIZE, m_axi_gmem2_AWBURST, 
  m_axi_gmem2_AWLOCK, m_axi_gmem2_AWCACHE, m_axi_gmem2_AWPROT, m_axi_gmem2_AWQOS, 
  m_axi_gmem2_AWREGION, m_axi_gmem2_AWUSER, m_axi_gmem2_WVALID, m_axi_gmem2_WREADY, 
  m_axi_gmem2_WDATA, m_axi_gmem2_WSTRB, m_axi_gmem2_WLAST, m_axi_gmem2_WID, 
  m_axi_gmem2_WUSER, m_axi_gmem2_ARVALID, m_axi_gmem2_ARREADY, m_axi_gmem2_ARADDR, 
  m_axi_gmem2_ARID, m_axi_gmem2_ARLEN, m_axi_gmem2_ARSIZE, m_axi_gmem2_ARBURST, 
  m_axi_gmem2_ARLOCK, m_axi_gmem2_ARCACHE, m_axi_gmem2_ARPROT, m_axi_gmem2_ARQOS, 
  m_axi_gmem2_ARREGION, m_axi_gmem2_ARUSER, m_axi_gmem2_RVALID, m_axi_gmem2_RREADY, 
  m_axi_gmem2_RDATA, m_axi_gmem2_RLAST, m_axi_gmem2_RID, m_axi_gmem2_RUSER, 
  m_axi_gmem2_RRESP, m_axi_gmem2_BVALID, m_axi_gmem2_BREADY, m_axi_gmem2_BRESP, 
  m_axi_gmem2_BID, m_axi_gmem2_BUSER, m_axi_gmem3_AWVALID, m_axi_gmem3_AWREADY, 
  m_axi_gmem3_AWADDR, m_axi_gmem3_AWID, m_axi_gmem3_AWLEN, m_axi_gmem3_AWSIZE, 
  m_axi_gmem3_AWBURST, m_axi_gmem3_AWLOCK, m_axi_gmem3_AWCACHE, m_axi_gmem3_AWPROT, 
  m_axi_gmem3_AWQOS, m_axi_gmem3_AWREGION, m_axi_gmem3_AWUSER, m_axi_gmem3_WVALID, 
  m_axi_gmem3_WREADY, m_axi_gmem3_WDATA, m_axi_gmem3_WSTRB, m_axi_gmem3_WLAST, 
  m_axi_gmem3_WID, m_axi_gmem3_WUSER, m_axi_gmem3_ARVALID, m_axi_gmem3_ARREADY, 
  m_axi_gmem3_ARADDR, m_axi_gmem3_ARID, m_axi_gmem3_ARLEN, m_axi_gmem3_ARSIZE, 
  m_axi_gmem3_ARBURST, m_axi_gmem3_ARLOCK, m_axi_gmem3_ARCACHE, m_axi_gmem3_ARPROT, 
  m_axi_gmem3_ARQOS, m_axi_gmem3_ARREGION, m_axi_gmem3_ARUSER, m_axi_gmem3_RVALID, 
  m_axi_gmem3_RREADY, m_axi_gmem3_RDATA, m_axi_gmem3_RLAST, m_axi_gmem3_RID, 
  m_axi_gmem3_RUSER, m_axi_gmem3_RRESP, m_axi_gmem3_BVALID, m_axi_gmem3_BREADY, 
  m_axi_gmem3_BRESP, m_axi_gmem3_BID, m_axi_gmem3_BUSER, m_axi_gmem4_AWVALID, 
  m_axi_gmem4_AWREADY, m_axi_gmem4_AWADDR, m_axi_gmem4_AWID, m_axi_gmem4_AWLEN, 
  m_axi_gmem4_AWSIZE, m_axi_gmem4_AWBURST, m_axi_gmem4_AWLOCK, m_axi_gmem4_AWCACHE, 
  m_axi_gmem4_AWPROT, m_axi_gmem4_AWQOS, m_axi_gmem4_AWREGION, m_axi_gmem4_AWUSER, 
  m_axi_gmem4_WVALID, m_axi_gmem4_WREADY, m_axi_gmem4_WDATA, m_axi_gmem4_WSTRB, 
  m_axi_gmem4_WLAST, m_axi_gmem4_WID, m_axi_gmem4_WUSER, m_axi_gmem4_ARVALID, 
  m_axi_gmem4_ARREADY, m_axi_gmem4_ARADDR, m_axi_gmem4_ARID, m_axi_gmem4_ARLEN, 
  m_axi_gmem4_ARSIZE, m_axi_gmem4_ARBURST, m_axi_gmem4_ARLOCK, m_axi_gmem4_ARCACHE, 
  m_axi_gmem4_ARPROT, m_axi_gmem4_ARQOS, m_axi_gmem4_ARREGION, m_axi_gmem4_ARUSER, 
  m_axi_gmem4_RVALID, m_axi_gmem4_RREADY, m_axi_gmem4_RDATA, m_axi_gmem4_RLAST, 
  m_axi_gmem4_RID, m_axi_gmem4_RUSER, m_axi_gmem4_RRESP, m_axi_gmem4_BVALID, 
  m_axi_gmem4_BREADY, m_axi_gmem4_BRESP, m_axi_gmem4_BID, m_axi_gmem4_BUSER, 
  s_axi_control_AWVALID, s_axi_control_AWREADY, s_axi_control_AWADDR, 
  s_axi_control_WVALID, s_axi_control_WREADY, s_axi_control_WDATA, s_axi_control_WSTRB, 
  s_axi_control_ARVALID, s_axi_control_ARREADY, s_axi_control_ARADDR, 
  s_axi_control_RVALID, s_axi_control_RREADY, s_axi_control_RDATA, s_axi_control_RRESP, 
  s_axi_control_BVALID, s_axi_control_BREADY, s_axi_control_BRESP, interrupt, 
  s_axi_control_r_AWVALID, s_axi_control_r_AWREADY, s_axi_control_r_AWADDR, 
  s_axi_control_r_WVALID, s_axi_control_r_WREADY, s_axi_control_r_WDATA, 
  s_axi_control_r_WSTRB, s_axi_control_r_ARVALID, s_axi_control_r_ARREADY, 
  s_axi_control_r_ARADDR, s_axi_control_r_RVALID, s_axi_control_r_RREADY, 
  s_axi_control_r_RDATA, s_axi_control_r_RRESP, s_axi_control_r_BVALID, 
  s_axi_control_r_BREADY, s_axi_control_r_BRESP, m_axi_in_0_ARADDR, m_axi_in_0_ARBURST, 
  m_axi_in_0_ARCACHE, m_axi_in_0_ARID, m_axi_in_0_ARLEN, m_axi_in_0_ARLOCK, 
  m_axi_in_0_ARPROT, m_axi_in_0_ARQOS, m_axi_in_0_ARREADY, m_axi_in_0_ARSIZE, 
  m_axi_in_0_ARVALID, m_axi_in_0_AWADDR, m_axi_in_0_AWBURST, m_axi_in_0_AWCACHE, 
  m_axi_in_0_AWID, m_axi_in_0_AWLEN, m_axi_in_0_AWLOCK, m_axi_in_0_AWPROT, 
  m_axi_in_0_AWQOS, m_axi_in_0_AWREADY, m_axi_in_0_AWSIZE, m_axi_in_0_AWVALID, 
  m_axi_in_0_BID, m_axi_in_0_BREADY, m_axi_in_0_BRESP, m_axi_in_0_BVALID, m_axi_in_0_RDATA, 
  m_axi_in_0_RID, m_axi_in_0_RLAST, m_axi_in_0_RREADY, m_axi_in_0_RRESP, m_axi_in_0_RVALID, 
  m_axi_in_0_WDATA, m_axi_in_0_WLAST, m_axi_in_0_WREADY, m_axi_in_0_WSTRB, 
  m_axi_in_0_WVALID, m_axi_in_1_ARADDR, m_axi_in_1_ARBURST, m_axi_in_1_ARCACHE, 
  m_axi_in_1_ARID, m_axi_in_1_ARLEN, m_axi_in_1_ARLOCK, m_axi_in_1_ARPROT, 
  m_axi_in_1_ARQOS, m_axi_in_1_ARREADY, m_axi_in_1_ARSIZE, m_axi_in_1_ARVALID, 
  m_axi_in_1_AWADDR, m_axi_in_1_AWBURST, m_axi_in_1_AWCACHE, m_axi_in_1_AWID, 
  m_axi_in_1_AWLEN, m_axi_in_1_AWLOCK, m_axi_in_1_AWPROT, m_axi_in_1_AWQOS, 
  m_axi_in_1_AWREADY, m_axi_in_1_AWSIZE, m_axi_in_1_AWVALID, m_axi_in_1_BID, 
  m_axi_in_1_BREADY, m_axi_in_1_BRESP, m_axi_in_1_BVALID, m_axi_in_1_RDATA, m_axi_in_1_RID, 
  m_axi_in_1_RLAST, m_axi_in_1_RREADY, m_axi_in_1_RRESP, m_axi_in_1_RVALID, 
  m_axi_in_1_WDATA, m_axi_in_1_WLAST, m_axi_in_1_WREADY, m_axi_in_1_WSTRB, 
  m_axi_in_1_WVALID, m_axi_in_2_ARADDR, m_axi_in_2_ARBURST, m_axi_in_2_ARCACHE, 
  m_axi_in_2_ARID, m_axi_in_2_ARLEN, m_axi_in_2_ARLOCK, m_axi_in_2_ARPROT, 
  m_axi_in_2_ARQOS, m_axi_in_2_ARREADY, m_axi_in_2_ARSIZE, m_axi_in_2_ARVALID, 
  m_axi_in_2_AWADDR, m_axi_in_2_AWBURST, m_axi_in_2_AWCACHE, m_axi_in_2_AWID, 
  m_axi_in_2_AWLEN, m_axi_in_2_AWLOCK, m_axi_in_2_AWPROT, m_axi_in_2_AWQOS, 
  m_axi_in_2_AWREADY, m_axi_in_2_AWSIZE, m_axi_in_2_AWVALID, m_axi_in_2_BID, 
  m_axi_in_2_BREADY, m_axi_in_2_BRESP, m_axi_in_2_BVALID, m_axi_in_2_RDATA, m_axi_in_2_RID, 
  m_axi_in_2_RLAST, m_axi_in_2_RREADY, m_axi_in_2_RRESP, m_axi_in_2_RVALID, 
  m_axi_in_2_WDATA, m_axi_in_2_WLAST, m_axi_in_2_WREADY, m_axi_in_2_WSTRB, 
  m_axi_in_2_WVALID, m_axi_in_3_ARADDR, m_axi_in_3_ARBURST, m_axi_in_3_ARCACHE, 
  m_axi_in_3_ARID, m_axi_in_3_ARLEN, m_axi_in_3_ARLOCK, m_axi_in_3_ARPROT, 
  m_axi_in_3_ARQOS, m_axi_in_3_ARREADY, m_axi_in_3_ARSIZE, m_axi_in_3_ARVALID, 
  m_axi_in_3_AWADDR, m_axi_in_3_AWBURST, m_axi_in_3_AWCACHE, m_axi_in_3_AWID, 
  m_axi_in_3_AWLEN, m_axi_in_3_AWLOCK, m_axi_in_3_AWPROT, m_axi_in_3_AWQOS, 
  m_axi_in_3_AWREADY, m_axi_in_3_AWSIZE, m_axi_in_3_AWVALID, m_axi_in_3_BID, 
  m_axi_in_3_BREADY, m_axi_in_3_BRESP, m_axi_in_3_BVALID, m_axi_in_3_RDATA, m_axi_in_3_RID, 
  m_axi_in_3_RLAST, m_axi_in_3_RREADY, m_axi_in_3_RRESP, m_axi_in_3_RVALID, 
  m_axi_in_3_WDATA, m_axi_in_3_WLAST, m_axi_in_3_WREADY, m_axi_in_3_WSTRB, 
  m_axi_in_3_WVALID, m_axi_final_out_ARADDR, m_axi_final_out_ARBURST, 
  m_axi_final_out_ARCACHE, m_axi_final_out_ARID, m_axi_final_out_ARLEN, 
  m_axi_final_out_ARLOCK, m_axi_final_out_ARPROT, m_axi_final_out_ARQOS, 
  m_axi_final_out_ARREADY, m_axi_final_out_ARSIZE, m_axi_final_out_ARVALID, 
  m_axi_final_out_AWADDR, m_axi_final_out_AWBURST, m_axi_final_out_AWCACHE, 
  m_axi_final_out_AWID, m_axi_final_out_AWLEN, m_axi_final_out_AWLOCK, 
  m_axi_final_out_AWPROT, m_axi_final_out_AWQOS, m_axi_final_out_AWREADY, 
  m_axi_final_out_AWSIZE, m_axi_final_out_AWVALID, m_axi_final_out_BID, 
  m_axi_final_out_BREADY, m_axi_final_out_BRESP, m_axi_final_out_BVALID, 
  m_axi_final_out_RDATA, m_axi_final_out_RID, m_axi_final_out_RLAST, 
  m_axi_final_out_RREADY, m_axi_final_out_RRESP, m_axi_final_out_RVALID, 
  m_axi_final_out_WDATA, m_axi_final_out_WLAST, m_axi_final_out_WREADY, 
  m_axi_final_out_WSTRB, m_axi_final_out_WVALID)
/* synthesis syn_black_box black_box_pad_pin="ap_rst_n,m_axi_gmem0_AWVALID,m_axi_gmem0_AWREADY,m_axi_gmem0_AWADDR[63:0],m_axi_gmem0_AWID[0:0],m_axi_gmem0_AWLEN[7:0],m_axi_gmem0_AWSIZE[2:0],m_axi_gmem0_AWBURST[1:0],m_axi_gmem0_AWLOCK[1:0],m_axi_gmem0_AWCACHE[3:0],m_axi_gmem0_AWPROT[2:0],m_axi_gmem0_AWQOS[3:0],m_axi_gmem0_AWREGION[3:0],m_axi_gmem0_AWUSER[0:0],m_axi_gmem0_WVALID,m_axi_gmem0_WREADY,m_axi_gmem0_WDATA[127:0],m_axi_gmem0_WSTRB[15:0],m_axi_gmem0_WLAST,m_axi_gmem0_WID[0:0],m_axi_gmem0_WUSER[0:0],m_axi_gmem0_ARVALID,m_axi_gmem0_ARREADY,m_axi_gmem0_ARADDR[63:0],m_axi_gmem0_ARID[0:0],m_axi_gmem0_ARLEN[7:0],m_axi_gmem0_ARSIZE[2:0],m_axi_gmem0_ARBURST[1:0],m_axi_gmem0_ARLOCK[1:0],m_axi_gmem0_ARCACHE[3:0],m_axi_gmem0_ARPROT[2:0],m_axi_gmem0_ARQOS[3:0],m_axi_gmem0_ARREGION[3:0],m_axi_gmem0_ARUSER[0:0],m_axi_gmem0_RVALID,m_axi_gmem0_RREADY,m_axi_gmem0_RDATA[127:0],m_axi_gmem0_RLAST,m_axi_gmem0_RID[0:0],m_axi_gmem0_RUSER[0:0],m_axi_gmem0_RRESP[1:0],m_axi_gmem0_BVALID,m_axi_gmem0_BREADY,m_axi_gmem0_BRESP[1:0],m_axi_gmem0_BID[0:0],m_axi_gmem0_BUSER[0:0],m_axi_gmem1_AWVALID,m_axi_gmem1_AWREADY,m_axi_gmem1_AWADDR[63:0],m_axi_gmem1_AWID[0:0],m_axi_gmem1_AWLEN[7:0],m_axi_gmem1_AWSIZE[2:0],m_axi_gmem1_AWBURST[1:0],m_axi_gmem1_AWLOCK[1:0],m_axi_gmem1_AWCACHE[3:0],m_axi_gmem1_AWPROT[2:0],m_axi_gmem1_AWQOS[3:0],m_axi_gmem1_AWREGION[3:0],m_axi_gmem1_AWUSER[0:0],m_axi_gmem1_WVALID,m_axi_gmem1_WREADY,m_axi_gmem1_WDATA[127:0],m_axi_gmem1_WSTRB[15:0],m_axi_gmem1_WLAST,m_axi_gmem1_WID[0:0],m_axi_gmem1_WUSER[0:0],m_axi_gmem1_ARVALID,m_axi_gmem1_ARREADY,m_axi_gmem1_ARADDR[63:0],m_axi_gmem1_ARID[0:0],m_axi_gmem1_ARLEN[7:0],m_axi_gmem1_ARSIZE[2:0],m_axi_gmem1_ARBURST[1:0],m_axi_gmem1_ARLOCK[1:0],m_axi_gmem1_ARCACHE[3:0],m_axi_gmem1_ARPROT[2:0],m_axi_gmem1_ARQOS[3:0],m_axi_gmem1_ARREGION[3:0],m_axi_gmem1_ARUSER[0:0],m_axi_gmem1_RVALID,m_axi_gmem1_RREADY,m_axi_gmem1_RDATA[127:0],m_axi_gmem1_RLAST,m_axi_gmem1_RID[0:0],m_axi_gmem1_RUSER[0:0],m_axi_gmem1_RRESP[1:0],m_axi_gmem1_BVALID,m_axi_gmem1_BREADY,m_axi_gmem1_BRESP[1:0],m_axi_gmem1_BID[0:0],m_axi_gmem1_BUSER[0:0],m_axi_gmem2_AWVALID,m_axi_gmem2_AWREADY,m_axi_gmem2_AWADDR[63:0],m_axi_gmem2_AWID[0:0],m_axi_gmem2_AWLEN[7:0],m_axi_gmem2_AWSIZE[2:0],m_axi_gmem2_AWBURST[1:0],m_axi_gmem2_AWLOCK[1:0],m_axi_gmem2_AWCACHE[3:0],m_axi_gmem2_AWPROT[2:0],m_axi_gmem2_AWQOS[3:0],m_axi_gmem2_AWREGION[3:0],m_axi_gmem2_AWUSER[0:0],m_axi_gmem2_WVALID,m_axi_gmem2_WREADY,m_axi_gmem2_WDATA[127:0],m_axi_gmem2_WSTRB[15:0],m_axi_gmem2_WLAST,m_axi_gmem2_WID[0:0],m_axi_gmem2_WUSER[0:0],m_axi_gmem2_ARVALID,m_axi_gmem2_ARREADY,m_axi_gmem2_ARADDR[63:0],m_axi_gmem2_ARID[0:0],m_axi_gmem2_ARLEN[7:0],m_axi_gmem2_ARSIZE[2:0],m_axi_gmem2_ARBURST[1:0],m_axi_gmem2_ARLOCK[1:0],m_axi_gmem2_ARCACHE[3:0],m_axi_gmem2_ARPROT[2:0],m_axi_gmem2_ARQOS[3:0],m_axi_gmem2_ARREGION[3:0],m_axi_gmem2_ARUSER[0:0],m_axi_gmem2_RVALID,m_axi_gmem2_RREADY,m_axi_gmem2_RDATA[127:0],m_axi_gmem2_RLAST,m_axi_gmem2_RID[0:0],m_axi_gmem2_RUSER[0:0],m_axi_gmem2_RRESP[1:0],m_axi_gmem2_BVALID,m_axi_gmem2_BREADY,m_axi_gmem2_BRESP[1:0],m_axi_gmem2_BID[0:0],m_axi_gmem2_BUSER[0:0],m_axi_gmem3_AWVALID,m_axi_gmem3_AWREADY,m_axi_gmem3_AWADDR[63:0],m_axi_gmem3_AWID[0:0],m_axi_gmem3_AWLEN[7:0],m_axi_gmem3_AWSIZE[2:0],m_axi_gmem3_AWBURST[1:0],m_axi_gmem3_AWLOCK[1:0],m_axi_gmem3_AWCACHE[3:0],m_axi_gmem3_AWPROT[2:0],m_axi_gmem3_AWQOS[3:0],m_axi_gmem3_AWREGION[3:0],m_axi_gmem3_AWUSER[0:0],m_axi_gmem3_WVALID,m_axi_gmem3_WREADY,m_axi_gmem3_WDATA[127:0],m_axi_gmem3_WSTRB[15:0],m_axi_gmem3_WLAST,m_axi_gmem3_WID[0:0],m_axi_gmem3_WUSER[0:0],m_axi_gmem3_ARVALID,m_axi_gmem3_ARREADY,m_axi_gmem3_ARADDR[63:0],m_axi_gmem3_ARID[0:0],m_axi_gmem3_ARLEN[7:0],m_axi_gmem3_ARSIZE[2:0],m_axi_gmem3_ARBURST[1:0],m_axi_gmem3_ARLOCK[1:0],m_axi_gmem3_ARCACHE[3:0],m_axi_gmem3_ARPROT[2:0],m_axi_gmem3_ARQOS[3:0],m_axi_gmem3_ARREGION[3:0],m_axi_gmem3_ARUSER[0:0],m_axi_gmem3_RVALID,m_axi_gmem3_RREADY,m_axi_gmem3_RDATA[127:0],m_axi_gmem3_RLAST,m_axi_gmem3_RID[0:0],m_axi_gmem3_RUSER[0:0],m_axi_gmem3_RRESP[1:0],m_axi_gmem3_BVALID,m_axi_gmem3_BREADY,m_axi_gmem3_BRESP[1:0],m_axi_gmem3_BID[0:0],m_axi_gmem3_BUSER[0:0],m_axi_gmem4_AWVALID,m_axi_gmem4_AWREADY,m_axi_gmem4_AWADDR[63:0],m_axi_gmem4_AWID[0:0],m_axi_gmem4_AWLEN[7:0],m_axi_gmem4_AWSIZE[2:0],m_axi_gmem4_AWBURST[1:0],m_axi_gmem4_AWLOCK[1:0],m_axi_gmem4_AWCACHE[3:0],m_axi_gmem4_AWPROT[2:0],m_axi_gmem4_AWQOS[3:0],m_axi_gmem4_AWREGION[3:0],m_axi_gmem4_AWUSER[0:0],m_axi_gmem4_WVALID,m_axi_gmem4_WREADY,m_axi_gmem4_WDATA[31:0],m_axi_gmem4_WSTRB[3:0],m_axi_gmem4_WLAST,m_axi_gmem4_WID[0:0],m_axi_gmem4_WUSER[0:0],m_axi_gmem4_ARVALID,m_axi_gmem4_ARREADY,m_axi_gmem4_ARADDR[63:0],m_axi_gmem4_ARID[0:0],m_axi_gmem4_ARLEN[7:0],m_axi_gmem4_ARSIZE[2:0],m_axi_gmem4_ARBURST[1:0],m_axi_gmem4_ARLOCK[1:0],m_axi_gmem4_ARCACHE[3:0],m_axi_gmem4_ARPROT[2:0],m_axi_gmem4_ARQOS[3:0],m_axi_gmem4_ARREGION[3:0],m_axi_gmem4_ARUSER[0:0],m_axi_gmem4_RVALID,m_axi_gmem4_RREADY,m_axi_gmem4_RDATA[31:0],m_axi_gmem4_RLAST,m_axi_gmem4_RID[0:0],m_axi_gmem4_RUSER[0:0],m_axi_gmem4_RRESP[1:0],m_axi_gmem4_BVALID,m_axi_gmem4_BREADY,m_axi_gmem4_BRESP[1:0],m_axi_gmem4_BID[0:0],m_axi_gmem4_BUSER[0:0],s_axi_control_AWVALID,s_axi_control_AWREADY,s_axi_control_AWADDR[3:0],s_axi_control_WVALID,s_axi_control_WREADY,s_axi_control_WDATA[31:0],s_axi_control_WSTRB[3:0],s_axi_control_ARVALID,s_axi_control_ARREADY,s_axi_control_ARADDR[3:0],s_axi_control_RVALID,s_axi_control_RREADY,s_axi_control_RDATA[31:0],s_axi_control_RRESP[1:0],s_axi_control_BVALID,s_axi_control_BREADY,s_axi_control_BRESP[1:0],interrupt,s_axi_control_r_AWVALID,s_axi_control_r_AWREADY,s_axi_control_r_AWADDR[6:0],s_axi_control_r_WVALID,s_axi_control_r_WREADY,s_axi_control_r_WDATA[31:0],s_axi_control_r_WSTRB[3:0],s_axi_control_r_ARVALID,s_axi_control_r_ARREADY,s_axi_control_r_ARADDR[6:0],s_axi_control_r_RVALID,s_axi_control_r_RREADY,s_axi_control_r_RDATA[31:0],s_axi_control_r_RRESP[1:0],s_axi_control_r_BVALID,s_axi_control_r_BREADY,s_axi_control_r_BRESP[1:0],m_axi_in_0_ARADDR[63:0],m_axi_in_0_ARBURST[1:0],m_axi_in_0_ARCACHE[3:0],m_axi_in_0_ARID[0:0],m_axi_in_0_ARLEN[7:0],m_axi_in_0_ARLOCK,m_axi_in_0_ARPROT[2:0],m_axi_in_0_ARQOS[3:0],m_axi_in_0_ARREADY,m_axi_in_0_ARSIZE[2:0],m_axi_in_0_ARVALID,m_axi_in_0_AWADDR[63:0],m_axi_in_0_AWBURST[1:0],m_axi_in_0_AWCACHE[3:0],m_axi_in_0_AWID[0:0],m_axi_in_0_AWLEN[7:0],m_axi_in_0_AWLOCK,m_axi_in_0_AWPROT[2:0],m_axi_in_0_AWQOS[3:0],m_axi_in_0_AWREADY,m_axi_in_0_AWSIZE[2:0],m_axi_in_0_AWVALID,m_axi_in_0_BID[0:0],m_axi_in_0_BREADY,m_axi_in_0_BRESP[1:0],m_axi_in_0_BVALID,m_axi_in_0_RDATA[127:0],m_axi_in_0_RID[0:0],m_axi_in_0_RLAST,m_axi_in_0_RREADY,m_axi_in_0_RRESP[1:0],m_axi_in_0_RVALID,m_axi_in_0_WDATA[127:0],m_axi_in_0_WLAST,m_axi_in_0_WREADY,m_axi_in_0_WSTRB[15:0],m_axi_in_0_WVALID,m_axi_in_1_ARADDR[63:0],m_axi_in_1_ARBURST[1:0],m_axi_in_1_ARCACHE[3:0],m_axi_in_1_ARID[0:0],m_axi_in_1_ARLEN[7:0],m_axi_in_1_ARLOCK,m_axi_in_1_ARPROT[2:0],m_axi_in_1_ARQOS[3:0],m_axi_in_1_ARREADY,m_axi_in_1_ARSIZE[2:0],m_axi_in_1_ARVALID,m_axi_in_1_AWADDR[63:0],m_axi_in_1_AWBURST[1:0],m_axi_in_1_AWCACHE[3:0],m_axi_in_1_AWID[0:0],m_axi_in_1_AWLEN[7:0],m_axi_in_1_AWLOCK,m_axi_in_1_AWPROT[2:0],m_axi_in_1_AWQOS[3:0],m_axi_in_1_AWREADY,m_axi_in_1_AWSIZE[2:0],m_axi_in_1_AWVALID,m_axi_in_1_BID[0:0],m_axi_in_1_BREADY,m_axi_in_1_BRESP[1:0],m_axi_in_1_BVALID,m_axi_in_1_RDATA[127:0],m_axi_in_1_RID[0:0],m_axi_in_1_RLAST,m_axi_in_1_RREADY,m_axi_in_1_RRESP[1:0],m_axi_in_1_RVALID,m_axi_in_1_WDATA[127:0],m_axi_in_1_WLAST,m_axi_in_1_WREADY,m_axi_in_1_WSTRB[15:0],m_axi_in_1_WVALID,m_axi_in_2_ARADDR[63:0],m_axi_in_2_ARBURST[1:0],m_axi_in_2_ARCACHE[3:0],m_axi_in_2_ARID[0:0],m_axi_in_2_ARLEN[7:0],m_axi_in_2_ARLOCK,m_axi_in_2_ARPROT[2:0],m_axi_in_2_ARQOS[3:0],m_axi_in_2_ARREADY,m_axi_in_2_ARSIZE[2:0],m_axi_in_2_ARVALID,m_axi_in_2_AWADDR[63:0],m_axi_in_2_AWBURST[1:0],m_axi_in_2_AWCACHE[3:0],m_axi_in_2_AWID[0:0],m_axi_in_2_AWLEN[7:0],m_axi_in_2_AWLOCK,m_axi_in_2_AWPROT[2:0],m_axi_in_2_AWQOS[3:0],m_axi_in_2_AWREADY,m_axi_in_2_AWSIZE[2:0],m_axi_in_2_AWVALID,m_axi_in_2_BID[0:0],m_axi_in_2_BREADY,m_axi_in_2_BRESP[1:0],m_axi_in_2_BVALID,m_axi_in_2_RDATA[127:0],m_axi_in_2_RID[0:0],m_axi_in_2_RLAST,m_axi_in_2_RREADY,m_axi_in_2_RRESP[1:0],m_axi_in_2_RVALID,m_axi_in_2_WDATA[127:0],m_axi_in_2_WLAST,m_axi_in_2_WREADY,m_axi_in_2_WSTRB[15:0],m_axi_in_2_WVALID,m_axi_in_3_ARADDR[63:0],m_axi_in_3_ARBURST[1:0],m_axi_in_3_ARCACHE[3:0],m_axi_in_3_ARID[0:0],m_axi_in_3_ARLEN[7:0],m_axi_in_3_ARLOCK,m_axi_in_3_ARPROT[2:0],m_axi_in_3_ARQOS[3:0],m_axi_in_3_ARREADY,m_axi_in_3_ARSIZE[2:0],m_axi_in_3_ARVALID,m_axi_in_3_AWADDR[63:0],m_axi_in_3_AWBURST[1:0],m_axi_in_3_AWCACHE[3:0],m_axi_in_3_AWID[0:0],m_axi_in_3_AWLEN[7:0],m_axi_in_3_AWLOCK,m_axi_in_3_AWPROT[2:0],m_axi_in_3_AWQOS[3:0],m_axi_in_3_AWREADY,m_axi_in_3_AWSIZE[2:0],m_axi_in_3_AWVALID,m_axi_in_3_BID[0:0],m_axi_in_3_BREADY,m_axi_in_3_BRESP[1:0],m_axi_in_3_BVALID,m_axi_in_3_RDATA[127:0],m_axi_in_3_RID[0:0],m_axi_in_3_RLAST,m_axi_in_3_RREADY,m_axi_in_3_RRESP[1:0],m_axi_in_3_RVALID,m_axi_in_3_WDATA[127:0],m_axi_in_3_WLAST,m_axi_in_3_WREADY,m_axi_in_3_WSTRB[15:0],m_axi_in_3_WVALID,m_axi_final_out_ARADDR[63:0],m_axi_final_out_ARBURST[1:0],m_axi_final_out_ARCACHE[3:0],m_axi_final_out_ARID[0:0],m_axi_final_out_ARLEN[7:0],m_axi_final_out_ARLOCK,m_axi_final_out_ARPROT[2:0],m_axi_final_out_ARQOS[3:0],m_axi_final_out_ARREADY,m_axi_final_out_ARSIZE[2:0],m_axi_final_out_ARVALID,m_axi_final_out_AWADDR[63:0],m_axi_final_out_AWBURST[1:0],m_axi_final_out_AWCACHE[3:0],m_axi_final_out_AWID[0:0],m_axi_final_out_AWLEN[7:0],m_axi_final_out_AWLOCK,m_axi_final_out_AWPROT[2:0],m_axi_final_out_AWQOS[3:0],m_axi_final_out_AWREADY,m_axi_final_out_AWSIZE[2:0],m_axi_final_out_AWVALID,m_axi_final_out_BID[0:0],m_axi_final_out_BREADY,m_axi_final_out_BRESP[1:0],m_axi_final_out_BVALID,m_axi_final_out_RDATA[31:0],m_axi_final_out_RID[0:0],m_axi_final_out_RLAST,m_axi_final_out_RREADY,m_axi_final_out_RRESP[1:0],m_axi_final_out_RVALID,m_axi_final_out_WDATA[31:0],m_axi_final_out_WLAST,m_axi_final_out_WREADY,m_axi_final_out_WSTRB[3:0],m_axi_final_out_WVALID" */
/* synthesis syn_force_seq_prim="ap_clk" */;
  input ap_clk /* synthesis syn_isclock = 1 */;
  input ap_rst_n;
  output m_axi_gmem0_AWVALID;
  input m_axi_gmem0_AWREADY;
  output [63:0]m_axi_gmem0_AWADDR;
  output [0:0]m_axi_gmem0_AWID;
  output [7:0]m_axi_gmem0_AWLEN;
  output [2:0]m_axi_gmem0_AWSIZE;
  output [1:0]m_axi_gmem0_AWBURST;
  output [1:0]m_axi_gmem0_AWLOCK;
  output [3:0]m_axi_gmem0_AWCACHE;
  output [2:0]m_axi_gmem0_AWPROT;
  output [3:0]m_axi_gmem0_AWQOS;
  output [3:0]m_axi_gmem0_AWREGION;
  output [0:0]m_axi_gmem0_AWUSER;
  output m_axi_gmem0_WVALID;
  input m_axi_gmem0_WREADY;
  output [127:0]m_axi_gmem0_WDATA;
  output [15:0]m_axi_gmem0_WSTRB;
  output m_axi_gmem0_WLAST;
  output [0:0]m_axi_gmem0_WID;
  output [0:0]m_axi_gmem0_WUSER;
  output m_axi_gmem0_ARVALID;
  input m_axi_gmem0_ARREADY;
  output [63:0]m_axi_gmem0_ARADDR;
  output [0:0]m_axi_gmem0_ARID;
  output [7:0]m_axi_gmem0_ARLEN;
  output [2:0]m_axi_gmem0_ARSIZE;
  output [1:0]m_axi_gmem0_ARBURST;
  output [1:0]m_axi_gmem0_ARLOCK;
  output [3:0]m_axi_gmem0_ARCACHE;
  output [2:0]m_axi_gmem0_ARPROT;
  output [3:0]m_axi_gmem0_ARQOS;
  output [3:0]m_axi_gmem0_ARREGION;
  output [0:0]m_axi_gmem0_ARUSER;
  input m_axi_gmem0_RVALID;
  output m_axi_gmem0_RREADY;
  input [127:0]m_axi_gmem0_RDATA;
  input m_axi_gmem0_RLAST;
  input [0:0]m_axi_gmem0_RID;
  input [0:0]m_axi_gmem0_RUSER;
  input [1:0]m_axi_gmem0_RRESP;
  input m_axi_gmem0_BVALID;
  output m_axi_gmem0_BREADY;
  input [1:0]m_axi_gmem0_BRESP;
  input [0:0]m_axi_gmem0_BID;
  input [0:0]m_axi_gmem0_BUSER;
  output m_axi_gmem1_AWVALID;
  input m_axi_gmem1_AWREADY;
  output [63:0]m_axi_gmem1_AWADDR;
  output [0:0]m_axi_gmem1_AWID;
  output [7:0]m_axi_gmem1_AWLEN;
  output [2:0]m_axi_gmem1_AWSIZE;
  output [1:0]m_axi_gmem1_AWBURST;
  output [1:0]m_axi_gmem1_AWLOCK;
  output [3:0]m_axi_gmem1_AWCACHE;
  output [2:0]m_axi_gmem1_AWPROT;
  output [3:0]m_axi_gmem1_AWQOS;
  output [3:0]m_axi_gmem1_AWREGION;
  output [0:0]m_axi_gmem1_AWUSER;
  output m_axi_gmem1_WVALID;
  input m_axi_gmem1_WREADY;
  output [127:0]m_axi_gmem1_WDATA;
  output [15:0]m_axi_gmem1_WSTRB;
  output m_axi_gmem1_WLAST;
  output [0:0]m_axi_gmem1_WID;
  output [0:0]m_axi_gmem1_WUSER;
  output m_axi_gmem1_ARVALID;
  input m_axi_gmem1_ARREADY;
  output [63:0]m_axi_gmem1_ARADDR;
  output [0:0]m_axi_gmem1_ARID;
  output [7:0]m_axi_gmem1_ARLEN;
  output [2:0]m_axi_gmem1_ARSIZE;
  output [1:0]m_axi_gmem1_ARBURST;
  output [1:0]m_axi_gmem1_ARLOCK;
  output [3:0]m_axi_gmem1_ARCACHE;
  output [2:0]m_axi_gmem1_ARPROT;
  output [3:0]m_axi_gmem1_ARQOS;
  output [3:0]m_axi_gmem1_ARREGION;
  output [0:0]m_axi_gmem1_ARUSER;
  input m_axi_gmem1_RVALID;
  output m_axi_gmem1_RREADY;
  input [127:0]m_axi_gmem1_RDATA;
  input m_axi_gmem1_RLAST;
  input [0:0]m_axi_gmem1_RID;
  input [0:0]m_axi_gmem1_RUSER;
  input [1:0]m_axi_gmem1_RRESP;
  input m_axi_gmem1_BVALID;
  output m_axi_gmem1_BREADY;
  input [1:0]m_axi_gmem1_BRESP;
  input [0:0]m_axi_gmem1_BID;
  input [0:0]m_axi_gmem1_BUSER;
  output m_axi_gmem2_AWVALID;
  input m_axi_gmem2_AWREADY;
  output [63:0]m_axi_gmem2_AWADDR;
  output [0:0]m_axi_gmem2_AWID;
  output [7:0]m_axi_gmem2_AWLEN;
  output [2:0]m_axi_gmem2_AWSIZE;
  output [1:0]m_axi_gmem2_AWBURST;
  output [1:0]m_axi_gmem2_AWLOCK;
  output [3:0]m_axi_gmem2_AWCACHE;
  output [2:0]m_axi_gmem2_AWPROT;
  output [3:0]m_axi_gmem2_AWQOS;
  output [3:0]m_axi_gmem2_AWREGION;
  output [0:0]m_axi_gmem2_AWUSER;
  output m_axi_gmem2_WVALID;
  input m_axi_gmem2_WREADY;
  output [127:0]m_axi_gmem2_WDATA;
  output [15:0]m_axi_gmem2_WSTRB;
  output m_axi_gmem2_WLAST;
  output [0:0]m_axi_gmem2_WID;
  output [0:0]m_axi_gmem2_WUSER;
  output m_axi_gmem2_ARVALID;
  input m_axi_gmem2_ARREADY;
  output [63:0]m_axi_gmem2_ARADDR;
  output [0:0]m_axi_gmem2_ARID;
  output [7:0]m_axi_gmem2_ARLEN;
  output [2:0]m_axi_gmem2_ARSIZE;
  output [1:0]m_axi_gmem2_ARBURST;
  output [1:0]m_axi_gmem2_ARLOCK;
  output [3:0]m_axi_gmem2_ARCACHE;
  output [2:0]m_axi_gmem2_ARPROT;
  output [3:0]m_axi_gmem2_ARQOS;
  output [3:0]m_axi_gmem2_ARREGION;
  output [0:0]m_axi_gmem2_ARUSER;
  input m_axi_gmem2_RVALID;
  output m_axi_gmem2_RREADY;
  input [127:0]m_axi_gmem2_RDATA;
  input m_axi_gmem2_RLAST;
  input [0:0]m_axi_gmem2_RID;
  input [0:0]m_axi_gmem2_RUSER;
  input [1:0]m_axi_gmem2_RRESP;
  input m_axi_gmem2_BVALID;
  output m_axi_gmem2_BREADY;
  input [1:0]m_axi_gmem2_BRESP;
  input [0:0]m_axi_gmem2_BID;
  input [0:0]m_axi_gmem2_BUSER;
  output m_axi_gmem3_AWVALID;
  input m_axi_gmem3_AWREADY;
  output [63:0]m_axi_gmem3_AWADDR;
  output [0:0]m_axi_gmem3_AWID;
  output [7:0]m_axi_gmem3_AWLEN;
  output [2:0]m_axi_gmem3_AWSIZE;
  output [1:0]m_axi_gmem3_AWBURST;
  output [1:0]m_axi_gmem3_AWLOCK;
  output [3:0]m_axi_gmem3_AWCACHE;
  output [2:0]m_axi_gmem3_AWPROT;
  output [3:0]m_axi_gmem3_AWQOS;
  output [3:0]m_axi_gmem3_AWREGION;
  output [0:0]m_axi_gmem3_AWUSER;
  output m_axi_gmem3_WVALID;
  input m_axi_gmem3_WREADY;
  output [127:0]m_axi_gmem3_WDATA;
  output [15:0]m_axi_gmem3_WSTRB;
  output m_axi_gmem3_WLAST;
  output [0:0]m_axi_gmem3_WID;
  output [0:0]m_axi_gmem3_WUSER;
  output m_axi_gmem3_ARVALID;
  input m_axi_gmem3_ARREADY;
  output [63:0]m_axi_gmem3_ARADDR;
  output [0:0]m_axi_gmem3_ARID;
  output [7:0]m_axi_gmem3_ARLEN;
  output [2:0]m_axi_gmem3_ARSIZE;
  output [1:0]m_axi_gmem3_ARBURST;
  output [1:0]m_axi_gmem3_ARLOCK;
  output [3:0]m_axi_gmem3_ARCACHE;
  output [2:0]m_axi_gmem3_ARPROT;
  output [3:0]m_axi_gmem3_ARQOS;
  output [3:0]m_axi_gmem3_ARREGION;
  output [0:0]m_axi_gmem3_ARUSER;
  input m_axi_gmem3_RVALID;
  output m_axi_gmem3_RREADY;
  input [127:0]m_axi_gmem3_RDATA;
  input m_axi_gmem3_RLAST;
  input [0:0]m_axi_gmem3_RID;
  input [0:0]m_axi_gmem3_RUSER;
  input [1:0]m_axi_gmem3_RRESP;
  input m_axi_gmem3_BVALID;
  output m_axi_gmem3_BREADY;
  input [1:0]m_axi_gmem3_BRESP;
  input [0:0]m_axi_gmem3_BID;
  input [0:0]m_axi_gmem3_BUSER;
  output m_axi_gmem4_AWVALID;
  input m_axi_gmem4_AWREADY;
  output [63:0]m_axi_gmem4_AWADDR;
  output [0:0]m_axi_gmem4_AWID;
  output [7:0]m_axi_gmem4_AWLEN;
  output [2:0]m_axi_gmem4_AWSIZE;
  output [1:0]m_axi_gmem4_AWBURST;
  output [1:0]m_axi_gmem4_AWLOCK;
  output [3:0]m_axi_gmem4_AWCACHE;
  output [2:0]m_axi_gmem4_AWPROT;
  output [3:0]m_axi_gmem4_AWQOS;
  output [3:0]m_axi_gmem4_AWREGION;
  output [0:0]m_axi_gmem4_AWUSER;
  output m_axi_gmem4_WVALID;
  input m_axi_gmem4_WREADY;
  output [31:0]m_axi_gmem4_WDATA;
  output [3:0]m_axi_gmem4_WSTRB;
  output m_axi_gmem4_WLAST;
  output [0:0]m_axi_gmem4_WID;
  output [0:0]m_axi_gmem4_WUSER;
  output m_axi_gmem4_ARVALID;
  input m_axi_gmem4_ARREADY;
  output [63:0]m_axi_gmem4_ARADDR;
  output [0:0]m_axi_gmem4_ARID;
  output [7:0]m_axi_gmem4_ARLEN;
  output [2:0]m_axi_gmem4_ARSIZE;
  output [1:0]m_axi_gmem4_ARBURST;
  output [1:0]m_axi_gmem4_ARLOCK;
  output [3:0]m_axi_gmem4_ARCACHE;
  output [2:0]m_axi_gmem4_ARPROT;
  output [3:0]m_axi_gmem4_ARQOS;
  output [3:0]m_axi_gmem4_ARREGION;
  output [0:0]m_axi_gmem4_ARUSER;
  input m_axi_gmem4_RVALID;
  output m_axi_gmem4_RREADY;
  input [31:0]m_axi_gmem4_RDATA;
  input m_axi_gmem4_RLAST;
  input [0:0]m_axi_gmem4_RID;
  input [0:0]m_axi_gmem4_RUSER;
  input [1:0]m_axi_gmem4_RRESP;
  input m_axi_gmem4_BVALID;
  output m_axi_gmem4_BREADY;
  input [1:0]m_axi_gmem4_BRESP;
  input [0:0]m_axi_gmem4_BID;
  input [0:0]m_axi_gmem4_BUSER;
  input s_axi_control_AWVALID;
  output s_axi_control_AWREADY;
  input [3:0]s_axi_control_AWADDR;
  input s_axi_control_WVALID;
  output s_axi_control_WREADY;
  input [31:0]s_axi_control_WDATA;
  input [3:0]s_axi_control_WSTRB;
  input s_axi_control_ARVALID;
  output s_axi_control_ARREADY;
  input [3:0]s_axi_control_ARADDR;
  output s_axi_control_RVALID;
  input s_axi_control_RREADY;
  output [31:0]s_axi_control_RDATA;
  output [1:0]s_axi_control_RRESP;
  output s_axi_control_BVALID;
  input s_axi_control_BREADY;
  output [1:0]s_axi_control_BRESP;
  output interrupt;
  input s_axi_control_r_AWVALID;
  output s_axi_control_r_AWREADY;
  input [6:0]s_axi_control_r_AWADDR;
  input s_axi_control_r_WVALID;
  output s_axi_control_r_WREADY;
  input [31:0]s_axi_control_r_WDATA;
  input [3:0]s_axi_control_r_WSTRB;
  input s_axi_control_r_ARVALID;
  output s_axi_control_r_ARREADY;
  input [6:0]s_axi_control_r_ARADDR;
  output s_axi_control_r_RVALID;
  input s_axi_control_r_RREADY;
  output [31:0]s_axi_control_r_RDATA;
  output [1:0]s_axi_control_r_RRESP;
  output s_axi_control_r_BVALID;
  input s_axi_control_r_BREADY;
  output [1:0]s_axi_control_r_BRESP;
  output [63:0]m_axi_in_0_ARADDR;
  output [1:0]m_axi_in_0_ARBURST;
  output [3:0]m_axi_in_0_ARCACHE;
  output [0:0]m_axi_in_0_ARID;
  output [7:0]m_axi_in_0_ARLEN;
  output m_axi_in_0_ARLOCK;
  output [2:0]m_axi_in_0_ARPROT;
  output [3:0]m_axi_in_0_ARQOS;
  input m_axi_in_0_ARREADY;
  output [2:0]m_axi_in_0_ARSIZE;
  output m_axi_in_0_ARVALID;
  output [63:0]m_axi_in_0_AWADDR;
  output [1:0]m_axi_in_0_AWBURST;
  output [3:0]m_axi_in_0_AWCACHE;
  output [0:0]m_axi_in_0_AWID;
  output [7:0]m_axi_in_0_AWLEN;
  output m_axi_in_0_AWLOCK;
  output [2:0]m_axi_in_0_AWPROT;
  output [3:0]m_axi_in_0_AWQOS;
  input m_axi_in_0_AWREADY;
  output [2:0]m_axi_in_0_AWSIZE;
  output m_axi_in_0_AWVALID;
  input [0:0]m_axi_in_0_BID;
  output m_axi_in_0_BREADY;
  input [1:0]m_axi_in_0_BRESP;
  input m_axi_in_0_BVALID;
  input [127:0]m_axi_in_0_RDATA;
  input [0:0]m_axi_in_0_RID;
  input m_axi_in_0_RLAST;
  output m_axi_in_0_RREADY;
  input [1:0]m_axi_in_0_RRESP;
  input m_axi_in_0_RVALID;
  output [127:0]m_axi_in_0_WDATA;
  output m_axi_in_0_WLAST;
  input m_axi_in_0_WREADY;
  output [15:0]m_axi_in_0_WSTRB;
  output m_axi_in_0_WVALID;
  output [63:0]m_axi_in_1_ARADDR;
  output [1:0]m_axi_in_1_ARBURST;
  output [3:0]m_axi_in_1_ARCACHE;
  output [0:0]m_axi_in_1_ARID;
  output [7:0]m_axi_in_1_ARLEN;
  output m_axi_in_1_ARLOCK;
  output [2:0]m_axi_in_1_ARPROT;
  output [3:0]m_axi_in_1_ARQOS;
  input m_axi_in_1_ARREADY;
  output [2:0]m_axi_in_1_ARSIZE;
  output m_axi_in_1_ARVALID;
  output [63:0]m_axi_in_1_AWADDR;
  output [1:0]m_axi_in_1_AWBURST;
  output [3:0]m_axi_in_1_AWCACHE;
  output [0:0]m_axi_in_1_AWID;
  output [7:0]m_axi_in_1_AWLEN;
  output m_axi_in_1_AWLOCK;
  output [2:0]m_axi_in_1_AWPROT;
  output [3:0]m_axi_in_1_AWQOS;
  input m_axi_in_1_AWREADY;
  output [2:0]m_axi_in_1_AWSIZE;
  output m_axi_in_1_AWVALID;
  input [0:0]m_axi_in_1_BID;
  output m_axi_in_1_BREADY;
  input [1:0]m_axi_in_1_BRESP;
  input m_axi_in_1_BVALID;
  input [127:0]m_axi_in_1_RDATA;
  input [0:0]m_axi_in_1_RID;
  input m_axi_in_1_RLAST;
  output m_axi_in_1_RREADY;
  input [1:0]m_axi_in_1_RRESP;
  input m_axi_in_1_RVALID;
  output [127:0]m_axi_in_1_WDATA;
  output m_axi_in_1_WLAST;
  input m_axi_in_1_WREADY;
  output [15:0]m_axi_in_1_WSTRB;
  output m_axi_in_1_WVALID;
  output [63:0]m_axi_in_2_ARADDR;
  output [1:0]m_axi_in_2_ARBURST;
  output [3:0]m_axi_in_2_ARCACHE;
  output [0:0]m_axi_in_2_ARID;
  output [7:0]m_axi_in_2_ARLEN;
  output m_axi_in_2_ARLOCK;
  output [2:0]m_axi_in_2_ARPROT;
  output [3:0]m_axi_in_2_ARQOS;
  input m_axi_in_2_ARREADY;
  output [2:0]m_axi_in_2_ARSIZE;
  output m_axi_in_2_ARVALID;
  output [63:0]m_axi_in_2_AWADDR;
  output [1:0]m_axi_in_2_AWBURST;
  output [3:0]m_axi_in_2_AWCACHE;
  output [0:0]m_axi_in_2_AWID;
  output [7:0]m_axi_in_2_AWLEN;
  output m_axi_in_2_AWLOCK;
  output [2:0]m_axi_in_2_AWPROT;
  output [3:0]m_axi_in_2_AWQOS;
  input m_axi_in_2_AWREADY;
  output [2:0]m_axi_in_2_AWSIZE;
  output m_axi_in_2_AWVALID;
  input [0:0]m_axi_in_2_BID;
  output m_axi_in_2_BREADY;
  input [1:0]m_axi_in_2_BRESP;
  input m_axi_in_2_BVALID;
  input [127:0]m_axi_in_2_RDATA;
  input [0:0]m_axi_in_2_RID;
  input m_axi_in_2_RLAST;
  output m_axi_in_2_RREADY;
  input [1:0]m_axi_in_2_RRESP;
  input m_axi_in_2_RVALID;
  output [127:0]m_axi_in_2_WDATA;
  output m_axi_in_2_WLAST;
  input m_axi_in_2_WREADY;
  output [15:0]m_axi_in_2_WSTRB;
  output m_axi_in_2_WVALID;
  output [63:0]m_axi_in_3_ARADDR;
  output [1:0]m_axi_in_3_ARBURST;
  output [3:0]m_axi_in_3_ARCACHE;
  output [0:0]m_axi_in_3_ARID;
  output [7:0]m_axi_in_3_ARLEN;
  output m_axi_in_3_ARLOCK;
  output [2:0]m_axi_in_3_ARPROT;
  output [3:0]m_axi_in_3_ARQOS;
  input m_axi_in_3_ARREADY;
  output [2:0]m_axi_in_3_ARSIZE;
  output m_axi_in_3_ARVALID;
  output [63:0]m_axi_in_3_AWADDR;
  output [1:0]m_axi_in_3_AWBURST;
  output [3:0]m_axi_in_3_AWCACHE;
  output [0:0]m_axi_in_3_AWID;
  output [7:0]m_axi_in_3_AWLEN;
  output m_axi_in_3_AWLOCK;
  output [2:0]m_axi_in_3_AWPROT;
  output [3:0]m_axi_in_3_AWQOS;
  input m_axi_in_3_AWREADY;
  output [2:0]m_axi_in_3_AWSIZE;
  output m_axi_in_3_AWVALID;
  input [0:0]m_axi_in_3_BID;
  output m_axi_in_3_BREADY;
  input [1:0]m_axi_in_3_BRESP;
  input m_axi_in_3_BVALID;
  input [127:0]m_axi_in_3_RDATA;
  input [0:0]m_axi_in_3_RID;
  input m_axi_in_3_RLAST;
  output m_axi_in_3_RREADY;
  input [1:0]m_axi_in_3_RRESP;
  input m_axi_in_3_RVALID;
  output [127:0]m_axi_in_3_WDATA;
  output m_axi_in_3_WLAST;
  input m_axi_in_3_WREADY;
  output [15:0]m_axi_in_3_WSTRB;
  output m_axi_in_3_WVALID;
  output [63:0]m_axi_final_out_ARADDR;
  output [1:0]m_axi_final_out_ARBURST;
  output [3:0]m_axi_final_out_ARCACHE;
  output [0:0]m_axi_final_out_ARID;
  output [7:0]m_axi_final_out_ARLEN;
  output m_axi_final_out_ARLOCK;
  output [2:0]m_axi_final_out_ARPROT;
  output [3:0]m_axi_final_out_ARQOS;
  input m_axi_final_out_ARREADY;
  output [2:0]m_axi_final_out_ARSIZE;
  output m_axi_final_out_ARVALID;
  output [63:0]m_axi_final_out_AWADDR;
  output [1:0]m_axi_final_out_AWBURST;
  output [3:0]m_axi_final_out_AWCACHE;
  output [0:0]m_axi_final_out_AWID;
  output [7:0]m_axi_final_out_AWLEN;
  output m_axi_final_out_AWLOCK;
  output [2:0]m_axi_final_out_AWPROT;
  output [3:0]m_axi_final_out_AWQOS;
  input m_axi_final_out_AWREADY;
  output [2:0]m_axi_final_out_AWSIZE;
  output m_axi_final_out_AWVALID;
  input [0:0]m_axi_final_out_BID;
  output m_axi_final_out_BREADY;
  input [1:0]m_axi_final_out_BRESP;
  input m_axi_final_out_BVALID;
  input [31:0]m_axi_final_out_RDATA;
  input [0:0]m_axi_final_out_RID;
  input m_axi_final_out_RLAST;
  output m_axi_final_out_RREADY;
  input [1:0]m_axi_final_out_RRESP;
  input m_axi_final_out_RVALID;
  output [31:0]m_axi_final_out_WDATA;
  output m_axi_final_out_WLAST;
  input m_axi_final_out_WREADY;
  output [3:0]m_axi_final_out_WSTRB;
  output m_axi_final_out_WVALID;
endmodule
