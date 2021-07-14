set(SOURCE ${QL_DESIGNS_DIR}/counter_16bit/counter_16bit.v)
add_file_target(FILE counter_16bit.pcf)

add_fpga_target(
  NAME pcf_option_test-umc22-adder
  TOP top
  BOARD qlf_k4n8-qlf_k4n8_umc22_slow_board
  INPUT_IO_FILE counter_16bit.pcf
  SOURCES ${SOURCE}
  EXPLICIT_ADD_FILE_TARGET
  )

add_dependencies(all_qlf_k4n8_tests_adder pcf_option_test-umc22-adder_bit)
