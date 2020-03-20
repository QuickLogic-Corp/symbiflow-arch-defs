# BASYS3 constraint files
add_file_target(FILE basys3.pcf)
add_file_target(FILE basys3.sdc)
add_file_target(FILE basys3_pmod.pcf)

# ARTY constraint files
add_file_target(FILE arty_uart.pcf)
add_file_target(FILE arty_swbut.pcf)

# ZYBO constraint files
add_file_target(FILE zybo.pcf)
add_file_target(FILE zyboz7.pcf)

# Nexys-video constraint files
add_file_target(FILE nexys_video.pcf)

add_file_target(FILE error_output_logic.v SCANNER_TYPE verilog)
add_file_target(FILE error_output_logic_unt.v SCANNER_TYPE verilog)
add_file_target(FILE error_output_logic_tb.v SCANNER_TYPE verilog)

add_fpga_target(
    NAME error_output_logic_test
    BOARD basys3
    INPUT_IO_FILE basys3.pcf
    SOURCES
        error_output_logic_unt.v
        error_output_logic.v
    TESTBENCH_SOURCES
        error_output_logic_tb.v
    EXPLICIT_ADD_FILE_TARGET
)

add_dependencies(all_xc7_tests
    testbench_error_output_logic_tb
    testbench_synth_error_output_logic_tb
    testbinch_error_output_logic_tb
    )

add_file_target(FILE ram_shifter.v SCANNER_TYPE verilog)
add_file_target(FILE ram_test.v SCANNER_TYPE verilog)
add_file_target(FILE rom_test.v SCANNER_TYPE verilog)