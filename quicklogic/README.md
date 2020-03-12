# SymbiFlow for Quicklogic FPGAs

## Quickstart guide

### 1. Installation of Yosys with QuickLogic support

First, download the sources from the Antmicro Yosys fork:

```
git clone https://github.com/antmicro/yosys.git -b quicklogic quicklogic-yosys
cd quicklogic-yosys
```

Then build Yosys with the following commands:

```
cd yosys
make config-gcc
make -j$(nproc)
sudo make install
```

This will install Yosys into your `/usr/bin/` directory.

Note: If you want to build Yosys using clang then replace `make config-gcc` with `make config-clang`.

Note: Once the changes in Yosys regarding QuickLogic are added to mainstream, this step will be unnecessary, since everything will be fetched by Anaconda.

### 2. SymbiFlow installation

Clone the SymbiFlow repository, make sure to use the `master+quicklogic` branch:

```
git clone https://github.com/antmicro/symbiflow-arch-defs -b master+quicklogic
```

Setup the environment:

```
export YOSYS=/usr/bin/yosys
# assuming default Yosys installation path
make env
cd build && make all_conda
```

### 3. Generate a bitstream for a sample design

Once the SymbiFlow environment is set you can perform the implementation (synthesis, placement and routing) of FPAG designs.

Go to the quicklogic/tests directory and choose a design you want to implement:

```
cd tests/btn_counter
make btn_counter-ql-chandalar_bit
```

This will generate a binary bitstream file for the design. The resulting bitstream will be written to the `top.bit` file in the working directory of the design.

Currently designs that work on hardware are:

- btn_xor-ql-chandalar
- btn_ff-ql-chandalar
- btn_counter-ql-chandalar

### 4. Programming the EOS S3 SoC

There are helper scripts integrated with the flow that can automatically configure the IOMUX of the SoC so that all top-level IO ports of the design are routed to the physical pads of the chip.

In order to generate the programming script build the following target:

```
make btn_counter-ql-chandalar_jlink
```

The script will contain the bitstream as well as IOMUX configuration.

## Limitations

1. No support for the global clock network yet. Clock signal is routed to *QCK* inputs of LOGIC cells via the ordinary routing network.
2. No support for dedicated connections between the FPGA and the SoC yet.