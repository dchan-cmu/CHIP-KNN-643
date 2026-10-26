.PHONY: help

help::
	$(ECHO) "Makefile Usage:"
	$(ECHO) "  make all TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform>"
	$(ECHO) "      Command to generate the design for specified Target and Shell."
	$(ECHO) ""
	$(ECHO) "  make clean "
	$(ECHO) "      Command to remove the generated non-hardware files."
	$(ECHO) ""
	$(ECHO) "  make cleanall"
	$(ECHO) "      Command to remove all the generated files."
	$(ECHO) ""
	$(ECHO) "  make check TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform>"
	$(ECHO) "      Command to run application in emulation."
	$(ECHO) ""
	$(ECHO) "  make build TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform>"
	$(ECHO) "      Command to build xclbin application."
	$(ECHO) ""

DEVICE := xilinx_u280_xdma_201920_3
# Points to top directory of Git repository
COMMON_REPO = ./
PWD = $(shell readlink -f .)
ABS_COMMON_REPO = $(shell readlink -f $(COMMON_REPO))

TARGET := hw
HOST_ARCH := x86

include ./utils.mk

XSA := $(call device2xsa, $(DEVICE))
TEMP_DIR := ./_x.$(TARGET).$(XSA)
BUILD_DIR := ./build_dir.$(TARGET).$(XSA)
CLANG_RES_INC := $(shell tapa-clang -print-resource-dir)/include
CXX_INC := $(shell ls -d /usr/include/c++/[0-9]* 2>/dev/null | tail -n 1)
CXX_ARCH_INC := $(shell ls -d /usr/include/c++/*/*-linux* 2>/dev/null | tail -n 1)

VPP := v++

#Include Libraries
include $(ABS_COMMON_REPO)/common/includes/opencl/opencl.mk
include $(ABS_COMMON_REPO)/common/includes/xcl2/xcl2.mk
CXXFLAGS += $(xcl2_CXXFLAGS)
LDFLAGS += $(xcl2_LDFLAGS)
HOST_SRCS += $(xcl2_SRCS)
CXXFLAGS += -pthread
CXXFLAGS += $(opencl_CXXFLAGS) -Wall -O3 -g -std=c++17
LDFLAGS += $(opencl_LDFLAGS)

HOST_SRCS += src/knn-host.cpp 
KNN_SRC = src/knn.cpp
# Host compiler global settings
CXXFLAGS += -fmessage-length=0
CXXFLAGS += -I /opt/xilinx/xrt/lib -I /localssd/Xilinx/Vitis_HLS/2021.2/include
LDFLAGS += -lrt -lstdc++ 
LDFLAGS += -ltapa -lfrt -lglog -lgflags

# Kernel compiler global settings
CLFLAGS += -t $(TARGET) --platform $(DEVICE) --save-temps --kernel_frequency 200
ifneq ($(TARGET), hw)
	CLFLAGS += -g
endif


ifeq ($(TARGET),$(filter $(TARGET),sw_emu))
	CHECK_DEPENDENCY=$(EXECUTABLE) emconfig
else
	CHECK_DEPENDENCY=all
endif

CONFIGFILE = src/krnl_config.h
INIFILE = src/knn.ini
# Kernel linker flags
LDCLFLAGS += --config src/knn.ini

EXECUTABLE = knn
CMD_ARGS = $(BUILD_DIR)/knn.xclbin
EMCONFIG_DIR = $(TEMP_DIR)

BINARY_CONTAINERS += $(BUILD_DIR)/knn.xclbin
BINARY_CONTAINER_knn_OBJS += $(TEMP_DIR)/knn.xo
CP = cp -rf

.PHONY: all clean cleanall docs emconfig
all: check-devices $(EXECUTABLE) $(BINARY_CONTAINERS) emconfig

.PHONY: exe
exe: $(EXECUTABLE)

.PHONY: build
build: $(BINARY_CONTAINERS)

# Building kernel
$(TEMP_DIR)/knn.xo: $(KNN_SRC)
	mkdir -p $(TEMP_DIR)
	mkdir -p build_script
	tapac \
	      --work-dir $(TEMP_DIR) \
	      --top Knn \
	      --part-num xczu3eg-sbva484-1-e \
	      --clock-period 5.00 \
	      -o $(TEMP_DIR)/knn.xo \
	      --enable-synth-util \
          --cflags=-U__SYNTHESIS__ \
          --cflags=-w \
          --cflags=-Wno-invalid-constexpr \
          --cflags=-Wno-error=invalid-constexpr \
          --cflags=-I$(shell pwd)/src \
          --cflags=-I$(CLANG_RES_INC) \
          --cflags=-I$(CXX_INC) \
          --cflags=-I$(CXX_ARCH_INC) \
          --cflags=-I/usr/include \
          --cflags=-I/usr/include/x86_64-linux-gnu \
          --cflags=-I$$XILINX_HLS/include \
          --cflags=-I$$XILINX_VITIS/include \
          --cflags=-I$(shell pwd)/../../.tapa/usr/include \
	      --max-parallel-synth-jobs 12 \
	      --run-tapacc \
	      $(KNN_SRC)
	python3 $(shell pwd)/../clean_graph_cflags.py $(TEMP_DIR)/graph.json
	tapac \
	      --work-dir $(TEMP_DIR) \
	      --top Knn \
	      --part-num xczu3eg-sbva484-1-e \
	      --clock-period 5.00 \
	      -o $(TEMP_DIR)/knn.xo \
	      --enable-synth-util \
	      --max-parallel-synth-jobs 12 \
	      --run-hls \
	      --generate-task-rtl \
	      --generate-top-rtl \
	      --pack-xo \
	      --connectivity $(INIFILE) \
	      --read-only-args in_.* \
	      --write-only-args final_out\
	      $(KNN_SRC)

$(BUILD_DIR)/knn.xclbin: $(BINARY_CONTAINER_knn_OBJS)
	mkdir -p $(BUILD_DIR)
	$(VPP) $(CLFLAGS) --temp_dir $(BUILD_DIR) -l $(LDCLFLAGS) -o'$@' $(+)

# Building Host
$(EXECUTABLE): check-xrt $(HOST_SRCS) $(HOST_HDRS)
	$(CXX) $(CXXFLAGS) $(HOST_SRCS) $(KNN_SRC) $(HOST_HDRS) -o '$@' $(LDFLAGS)

emconfig:$(EMCONFIG_DIR)/emconfig.json
$(EMCONFIG_DIR)/emconfig.json:
	emconfigutil --platform $(DEVICE) --od $(EMCONFIG_DIR)

check: $(CHECK_DEPENDENCY)
	@echo $(CHECK_DEPENDENCY)
ifeq ($(TARGET),$(filter $(TARGET),sw_emu))
	$(CP) $(EMCONFIG_DIR)/emconfig.json .
	XCL_EMULATION_MODE=$(TARGET) ./$(EXECUTABLE)
else ifeq ($(TARGET),$(filter $(TARGET),hw_emu))
	$(CP) $(EMCONFIG_DIR)/emconfig.json .
	XCL_EMULATION_MODE=$(TARGET) ./$(EXECUTABLE) --bitstream=$(BUILD_DIR)/knn.xclbin
else
	./$(EXECUTABLE) $(BUILD_DIR)/knn.xclbin
endif

tapa_HLS: $(TEMP_DIR)/knn.xo

# Cleaning stuff
clean:
	-$(RMDIR) $(EXECUTABLE) 
	-$(RMDIR) profile_* TempConfig system_estimate.xtxt *.rpt *.csv 
	-$(RMDIR) src/*.ll *v++* .Xil emconfig.json dltmp* xmltmp* *.log *.jou *.wcfg *.wdb

cleanall: clean
	-$(RMDIR) build_dir* sd_card*
	-$(RMDIR) _x.* *xclbin.run_summary qemu-memory-_* emulation/ _vimage/ pl* start_simulation.sh *.xclbin
