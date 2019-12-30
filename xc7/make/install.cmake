function(DEFINE_XC7_TOOLCHAIN_TARGET)
  set(options)
  set(oneValueArgs ARCH CONV_SCRIPT SYNTH_SCRIPT BIT_TO_BIN ROUTE_CHAN_WIDTH)
  set(multiValueArgs VPR_ARCH_ARGS)

  cmake_parse_arguments(
    DEFINE_XC7_TOOLCHAIN_TARGET
    "${options}"
    "${oneValueArgs}"
    "${multiValueArgs}"
    "${ARGN}"
  )

  get_target_property_required(YOSYS env YOSYS)
  get_target_property(YOSYS_TARGET env YOSYS_TARGET)
  get_target_property_required(VPR env VPR)
  get_target_property(VPR_TARGET env VPR_TARGET)
  get_target_property_required(GENFASM env GENFASM)
  get_target_property(GENFASM_TARGET env GENFASM_TARGET)

  set(ARCH ${DEFINE_XC7_TOOLCHAIN_TARGET_ARCH})
  set(VPR_ARCH_ARGS ${DEFINE_XC7_TOOLCHAIN_TARGET_VPR_ARCH_ARGS})
  set(ROUTE_CHAN_WIDTH ${DEFINE_XC7_TOOLCHAIN_TARGET_ROUTE_CHAN_WIDTH})
  list(JOIN VPR_BASE_ARGS " " VPR_BASE_ARGS)
  string(JOIN " " VPR_ARGS ${VPR_BASE_ARGS} "--route_chan_width ${ROUTE_CHAN_WIDTH}" ${VPR_ARCH_ARGS})
  get_target_property_required(FASM_TO_BIT ${ARCH} FASM_TO_BIT)

  set(YOSYS_BINS "${YOSYS}" "${YOSYS}-abc" "${YOSYS}-smtbmc" "${YOSYS}-filterlib" "${YOSYS}-config")
  set(WRAPPERS env generate_constrains pack place route synth write_bitstream write_fasm)
  set(TOOLCHAIN_WRAPPERS)

  foreach(WRAPPER ${WRAPPERS})
    set(WRAPPER_PATH "${symbiflow-arch-defs_SOURCE_DIR}/xc7/toolchain_wrappers/${WRAPPER}")
    list(APPEND TOOLCHAIN_WRAPPERS ${WRAPPER_PATH})
  endforeach()

  set(VPR_COMMON_TEMPLATE "${symbiflow-arch-defs_SOURCE_DIR}/xc7/toolchain_wrappers/vpr_common")
  set(VPR_COMMON "${CMAKE_CURRENT_BINARY_DIR}/vpr_common")
  configure_file(${VPR_COMMON_TEMPLATE} "${VPR_COMMON}" @ONLY)

  install(FILES ${TOOLCHAIN_WRAPPERS} ${VPR_COMMON}
          DESTINATION bin
          PERMISSIONS WORLD_EXECUTE WORLD_READ OWNER_WRITE OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE)

  # install binaries
  install(FILES ${YOSYS_BINS} ${VPR} ${GENFASM}
          DESTINATION bin
          PERMISSIONS WORLD_EXECUTE WORLD_READ OWNER_WRITE OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE)

  install(TARGETS ${DEFINE_XC7_TOOLCHAIN_TARGET_BIT_TO_BIN}
          RUNTIME
          DESTINATION bin
          PERMISSIONS WORLD_EXECUTE WORLD_READ OWNER_WRITE OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE)

  # install python scripts
  install(FILES ${FASM_TO_BIT}
          DESTINATION bin/python
          PERMISSIONS WORLD_EXECUTE WORLD_READ OWNER_WRITE OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE)

  install(DIRECTORY ${symbiflow-arch-defs_SOURCE_DIR}/third_party/fasm
          DESTINATION bin/python)

  install(DIRECTORY ${symbiflow-arch-defs_SOURCE_DIR}/third_party/prjxray/prjxray
          DESTINATION bin/python/prjxray)

  install(DIRECTORY ${symbiflow-arch-defs_SOURCE_DIR}/third_party/prjxray/utils
          DESTINATION bin/python/prjxray)

  install(FILES ${symbiflow-arch-defs_SOURCE_DIR}/utils/lib/parse_pcf.py
          DESTINATION bin/python/lib)

  # install yosys data
  install(DIRECTORY ${YOSYS_DATADIR}
          DESTINATION share)

  # install prjxray techmap
  install(DIRECTORY ${symbiflow-arch-defs_SOURCE_DIR}/xc7/techmap
          DESTINATION share/prjxray)

  # install prjxray database
  install(DIRECTORY ${PRJXRAY_DB_DIR}
          DESTINATION share/prjxray)

  # install Yosys scripts
  install(FILES  ${DEFINE_XC7_TOOLCHAIN_TARGET_CONV_SCRIPT}
          DESTINATION share/prjxray)

  get_filename_component(YOSYS_SYNTH_SCRIPT_FILE ${DEFINE_XC7_TOOLCHAIN_TARGET_SYNTH_SCRIPT} NAME)
  get_filename_component(YOSYS_SYNTH_SCRIPT_PATH ${DEFINE_XC7_TOOLCHAIN_TARGET_SYNTH_SCRIPT} DIRECTORY)

  install(FILES "${YOSYS_SYNTH_SCRIPT_PATH}/install_${YOSYS_SYNTH_SCRIPT_FILE}"
          DESTINATION share/prjxray
          RENAME ${YOSYS_SYNTH_SCRIPT_FILE})

endfunction()

function(DEFINE_XC7_PINMAP_CSV_INSTALL_TARGET)
  set(options)
  set(oneValueArgs BOARD DEVICE PACKAGE)
  set(multiValueArgs)

  cmake_parse_arguments(
    DEFINE_XC7_PINMAP_CSV_INSTALL_TARGET
    "${options}"
    "${oneValueArgs}"
    "${multiValueArgs}"
    "${ARGN}"
  )

  set(BOARD ${DEFINE_XC7_PINMAP_CSV_INSTALL_TARGET_BOARD})
  set(DEVICE ${DEFINE_XC7_PINMAP_CSV_INSTALL_TARGET_DEVICE})
  set(PACKAGE ${DEFINE_XC7_PINMAP_CSV_INSTALL_TARGET_PACKAGE})

  get_target_property(USE_ROI ${DEVICE} USE_ROI)
  if(USE_ROI OR USE_ROI STREQUAL "USE_ROI-NOTFOUND")
    return()
  endif()

  get_target_property_required(PINMAP ${BOARD} PINMAP)
  get_file_location(PINMAP_FILE ${PINMAP})
  get_filename_component(PINMAP_FILE_NAME ${PINMAP_FILE} NAME)
  append_file_dependency(DEPS ${PINMAP})
  add_custom_target(
    "PINMAP_INSTALL_${BOARD}_${DEVICE}_${PACKAGE}_${PINMAP_FILE_NAME}"
    ALL
    DEPENDS ${DEPS}
    )
  install(FILES ${PINMAP_FILE}
      DESTINATION "share/arch/${DEVICE}_${PACKAGE}"
      RENAME "pinmap.csv")
endfunction()
