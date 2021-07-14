set(CLK_TREE ${QL_DESIGNS_DIR}/clock_tree_design/clock_tree_design.v)
add_file_target(FILE ${CLK_TREE} SCANNER_TYPE verilog)

add_fpga_target(
  NAME clock_tree_design_test-gf12-no-adder
  TOP clock_tree_design
  BOARD qlf_k6n10-qlf_k6n10_gf12_board
  SOURCES ${CLK_TREE}
  EXPLICIT_ADD_FILE_TARGET
  DEFINES SYNTH_OPTS=-no_adder
  )

add_fpga_target(
  NAME clock_tree_design_test-gf12-adder
  TOP clock_tree_design
  BOARD qlf_k6n10-qlf_k6n10_gf12_board
  SOURCES ${CLK_TREE}
  EXPLICIT_ADD_FILE_TARGET
  )

add_dependencies(all_qlf_k6n10_tests_no_adder clock_tree_design_test-gf12-no-adder_route)
add_dependencies(all_qlf_k6n10_tests_adder    clock_tree_design_test-gf12-adder_route)
