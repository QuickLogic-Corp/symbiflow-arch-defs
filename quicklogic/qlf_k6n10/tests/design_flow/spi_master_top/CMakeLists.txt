set(SPI_MASTER ${QL_DESIGNS_DIR}/spi_master_top/spi_master_top.v)
set(FILE1 ${QL_DESIGNS_DIR}/spi_master_top/baud_generator.v)
set(FILE2 ${QL_DESIGNS_DIR}/spi_master_top/ql_clkgate_x4.v)
set(FILE3 ${QL_DESIGNS_DIR}/spi_master_top/ql_mux2_x2.v)
set(FILE4 ${QL_DESIGNS_DIR}/spi_master_top/registers.v)
set(FILE5 ${QL_DESIGNS_DIR}/spi_master_top/serializer_deserializer.v)

add_file_target(FILE ${SPI_MASTER} SCANNER_TYPE verilog)
add_file_target(FILE ${FILE1} SCANNER_TYPE verilog)
add_file_target(FILE ${FILE2} SCANNER_TYPE verilog)
add_file_target(FILE ${FILE3} SCANNER_TYPE verilog)
add_file_target(FILE ${FILE4} SCANNER_TYPE verilog)
add_file_target(FILE ${FILE5} SCANNER_TYPE verilog)

add_fpga_target(
  NAME spi_master_top_test-gf12-no-adder
  TOP spi_master_top
  BOARD qlf_k6n10-qlf_k6n10_gf12_board
  SOURCES ${SPI_MASTER} ${FILE1} ${FILE2} ${FILE3} ${FILE4} ${FILE5} 
  EXPLICIT_ADD_FILE_TARGET
  DEFINES SYNTH_OPTS=-no_adder
  )

add_fpga_target(
  NAME spi_master_top_test-gf12-adder
  TOP spi_master_top
  BOARD qlf_k6n10-qlf_k6n10_gf12_board
  SOURCES ${SPI_MASTER} ${FILE1} ${FILE2} ${FILE3} ${FILE4} ${FILE5} 
  EXPLICIT_ADD_FILE_TARGET
  )

add_dependencies(all_qlf_k6n10_tests_no_adder spi_master_top_test-gf12-no-adder_route)
add_dependencies(all_qlf_k6n10_tests_adder    spi_master_top_test-gf12-adder_route)
