set(SOURCE ${QL_DESIGNS_DIR}/counter_4clk/counter_4clk.v)
add_file_target(FILE counter_4clk.pcf)

add_fpga_target(
  NAME clk_pcf_verify_test-umc22-adder
  TOP top
  BOARD qlf_k4n8-qlf_k4n8_umc22_slow_board
  SOURCES ${SOURCE}
  INPUT_IO_FILE counter_4clk.pcf
  EXPLICIT_ADD_FILE_TARGET
  NET_PATCH_EXTRA_ARGS "--pcf-constraints ${CMAKE_CURRENT_SOURCE_DIR}/counter_4clk.pcf"

  )

add_dependencies(all_qlf_k4n8_tests_adder clk_pcf_verify_test-umc22-adder_bit)
