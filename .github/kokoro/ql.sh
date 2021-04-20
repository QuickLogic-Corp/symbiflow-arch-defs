#!/bin/bash

SCRIPT_SRC="$(realpath ${BASH_SOURCE[0]})"
SCRIPT_DIR="$(dirname "${SCRIPT_SRC}")"
INSTALL_DIR="$(pwd)/github/${KOKORO_DIR}/install"

export CMAKE_FLAGS="-GNinja -DINSTALL_FAMILIES=qlf_k4n8 -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR}"
export BUILD_TOOL=ninja
source ${SCRIPT_DIR}/common.sh

source ${SCRIPT_DIR}/steps/start_monitor.sh

echo
echo "============================================================"
echo "Running quicklogic OpenFPGA tests (make all_quicklogic_tests)"
echo "------------------------------------------------------------"

set +e
(
	set -e
	source env/conda/bin/activate symbiflow_arch_def_base
	pushd build
	export VPR_NUM_WORKERS=${CORES}
	set +e
	ninja -j${MAX_CORES} all_qlf_k4n8_tests_adder
	BUILD_RESULT=$?
	# FIXME: Not sure if the below will work for QuickLogic now.
	#ninja print_qor > ql_openfpga_qor.csv
	# Installing devices and toolchain
	ninja -j${MAX_CORES} install
	popd
	exit ${BUILD_RESULT}
)
BUILD_RESULT=$?
set -e

echo
echo "========================================"
echo "Compressing and uploading install dir"
echo "----------------------------------------"
(
	du -ah install
	export GIT_HASH=$(git rev-parse --short HEAD)
	tar -I "pixz" -cvf symbiflow-quicklogic-${GIT_HASH}.tar.xz -C install bin share
)
echo "----------------------------------------"

source ${SCRIPT_DIR}/steps/stop_monitor.sh
exit $BUILD_RESULT

