#!/usr/bin/env python3

"""\
Convert a Verilog simulation model to a VPR `pb_type.xml`

The following are allowed on a top level module:

    - `(* TYPE="bel|blackbox" *)` : specify the type of the module
    (either a Basic ELement or a blackbox named after the pb_type

    - `(* CLASS="lut|routing|flipflop|mem" *)` : specify the class of an given
    instance. Must be specified for BELs

    - `(* ALTERNATIVE_TO="module" *)` : specify the module is one of several
    modes of another module (i.e. a <mode> in the pb_type). Note that all modes
    must be visible at the time of pb_type generation.

The following are allowed on nets within modules (TODO: use proper Verilog timing):
    - `(* SETUP="clk 10e-12" *)` : specify setup time for a given clock

    - `(* HOLD="clk 10e-12" *)` : specify hold time for a given clock

    - `(* CLK_TO_Q="clk 10e-12" *)` : specify clock-to-output time for a given clock

    - `(* DELAY_CONST_{input}="30e-12" *)` : specify a constant max delay from an input (applied to the output)

    - `(* DELAY_MATRIX_{input}="30e-12 35e-12; 20e-12 25e-12; ..." *)` : specify a VPR
        delay matrix (semicolons indicate rows). In this format columns specify
        inputs bits and rows specify output bits. This should be applied to the output.

The following are allowed on ports:
    - `(* CLOCK *)` : force a given port to be a clock

    - `(* ASSOC_CLOCK="RDCLK" *)` : force a port's associated clock to a given value

    - `(* PORT_CLASS="clock" *)` : specify the VPR "port_class"
"""

import yosys.run
import lxml.etree as ET
import argparse, re
import os, tempfile, sys
from yosys.json import YosysJson


parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument(
    'infiles',
    metavar='input.v', type=str, nargs='+',
    help="""\
One or more Verilog input files, that will be passed to Yosys internally.
They should be enough to generate a flattened representation of the model,
so that paths through the model can be determined.
""")
parser.add_argument(
    '--top',
    help="""\
Top level module, not needed if only one module exists across all input Verilog
files, in which case that module will be used as the top level.
""")
parser.add_argument(
    '-o',
    help="""\
Output filename, default 'model.xml'
""")

args = parser.parse_args()

vjson = yosys.run.vlog_to_json(args.infiles, False, False)
yj = YosysJson(vjson)

xi_url = "http://www.w3.org/2001/XInclude"
ET.register_namespace('xi', xi_url)
xi_include = "{%s}include" % xi_url

def include_xml(parent, href):
    return ET.SubElement(parent, xi_include, {'href': href})

if args.top is not None:
    top = args.top
else:
    top = yj.top

if top is None:
    print("ERROR: more than one module in design, cannot detect top level. Manually specify the top level module using --top")
    sys.exit(1)

tmod = yj.module(top)

def make_pb_content(mod, xml_parent):
    """Build the pb_type content - child pb_types, timing and direct interconnect,
    but not IO. This may be put directly inside <pb_type>, or inside <mode>."""
    def get_full_pin_name(pin):
        cname, cellpin = pin
        if cname != mod.name:
            cname = mod.cell_type(cname)
        return ("%s.%s" % (cname, cellpin))

    def make_direct_conn(ic_xml, source, dest):
        source_pin = get_full_pin_name(source)
        dest_pin = get_full_pin_name(dest)
        ic_name = dest_pin.replace(".","_")
        dir_xml = ET.SubElement(ic_xml, 'direct', {
            'name': ic_name,
            'input': source_pin,
            'output': dest_pin
        })
    # List of entries in format ((from_cell, from_pin), (to_cell, to_pin))
    interconn = []

    # Process cells. First build the list of cnames.
    for cname, i_of in mod.cells:
        pb_name = i_of
        module_path = os.path.dirname(yj.get_module_file(i_of))
        pb_type_path = "%s/pb_type.xml" % module_path
        include_xml(xml_parent, pb_type_path)
        # In order to avoid overspecifying interconnect, there are two directions we currently
        # consider. All interconnect going INTO a cell, and interconnect going out of a cell
        # into a top level output - or all outputs if "mode" is used.
        inp_cons = mod.cell_conns(cname, "input")
        for pin, net in inp_cons:
            drvs = mod.net_drivers(net)
            if len(drvs) == 0:
                print("ERROR: pin %s.%s has no driver, interconnect will be missing" % (pb_name, pin))
                assert False
            elif len(drvs) > 1:
                print("ERROR: pin %s.%s has multiple drivers, interconnect will be overspecified" % (pb_name, pin))
                assert False
            for drv_cell, drv_pin in drvs:
                interconn.append(((drv_cell, drv_pin), (cname, pin)))

        out_cons = mod.cell_conns(cname, "output")
        for pin, net in out_cons:
            sinks = mod.net_sinks(net)
            for sink_cell, sink_pin in sinks:
                if sink_cell == mod.name:
                     #Only consider outputs from cell to top level IO. Inputs to other cells will be dealt with
                     #in those cells.
                    interconn.append(((cname, pin), (sink_cell, sink_pin)))

    ic_xml = ET.SubElement(xml_parent, "interconnect")
    # Process interconnect
    for source, dest in interconn:
        make_direct_conn(ic_xml, source, dest)

    def process_clocked_tmg(tmgspec, port, xmltype, xml_parent):
        """Add a suitable timing spec if necessary to the pb_type"""
        if tmgspec is not None:
            splitspec = tmgspec.split(" ")
            assert len(splitspec) == 2
            attrs = {"port": port, "clock": splitspec[0]}
            if xmltype == "T_clock_to_Q":
                attrs["max"] = splitspec[1]
            else:
                attrs["value"] = splitspec[1]
            ET.SubElement(xml_parent, xmltype, attrs)

    # Process timing
    for name, width, iodir in mod.ports:
        port = "%s.%s" % (mod.name, name)
        # Clocked timing
        Tsetup = mod.net_attr(name, "SETUP")
        Thold = mod.net_attr(name, "HOLD")
        Tctoq = mod.net_attr(name, "CLK_TO_Q")
        process_clocked_tmg(Tsetup, port, "T_setup", xml_parent)
        process_clocked_tmg(Thold, port, "T_hold", xml_parent)
        process_clocked_tmg(Tctoq, port, "T_clock_to_Q", xml_parent)

        # Combinational delays
        dly_prefix = "DELAY_CONST_"
        dly_mat_prefix = "DELAY_MATRIX_"
        for attr, atvalue in mod.net_attrs(name).items():
            if attr.startswith(dly_prefix):
                # Single, constant delays
                inp = attr[len(dly_prefix):]
                inport = "%s.%s" % (mod.name, inp)
                ET.SubElement(xml_parent, "delay_constant", {
                    "in_port": inport,
                    "out_port": port,
                    "max": str(atvalue)
                })
            elif attr.startswith(dly_mat_prefix):
                # Constant delay matrices
                inp = attr[len(dly_mat_prefix):]
                inport = "%s.%s" % (mod.name, inp)
                mat = "\n" + atvalue.replace(";", "\n") + "\n"
                xml_mat = ET.SubElement(xml_parent, "delay_matrix", {
                    "in_port": inport,
                    "out_port": port,
                    "type": "max"
                })
                xml_mat.text = mat

def make_pb_type(mod):
    """Build the pb_type for a given module. mod is the YosysModule object to
    generate."""

    attrs = mod.module_attrs
    pb_xml_attrs = dict()

    pb_xml_attrs["name"] = mod.name

    # Process type and class of module
    mod_type = mod.attr("TYPE")
    mod_cls = mod.attr("CLASS")
    if mod_type == "bel":
        assert mod_cls is not None
        if mod_cls == "lut":
            pb_xml_attrs["blif_model"] = ".names"
            pb_xml_attrs["class"] = "lut"
        elif mod_cls == "routing":
            # TODO: pb_xml_attrs["class"] = "routing"
            pass
        elif mod_cls == "flipflop":
            pb_xml_attrs["blif_model"] = ".latch"
            pb_xml_attrs["class"] = "flipflop"
        else:
            assert False
    elif mod_type == "blackbox":
        pb_xml_attrs["blif_model"] = ".subckt " + mod.name
        if mod_cls is not None:
            if mod_cls == "mem":
                pb_xml_attrs["class"] = "memory"
            else:
                assert False
    elif mod_type is None:
        pass
    else:
        assert False

    #TODO: might not always be the case? should be use Verilog `generate`s to detect this?
    pb_xml_attrs["num_pb"] = "1"
    pb_type_xml = ET.Element("pb_type", pb_xml_attrs, nsmap = {'xi': xi_url})

    # Process IOs
    clocks = yosys.run.list_clocks(args.infiles, mod.name)
    for name, width, iodir in mod.ports:
        ioattrs = {"name": name, "num_pins": str(width), "equivalent": "false"}
        pclass = mod.net_attr(name, "PORT_CLASS")
        if pclass is not None:
            ioattrs["port_class"] = pclass
        if name in clocks:
            ET.SubElement(pb_type_xml, "clock", ioattrs)
        elif iodir == "input":
            ET.SubElement(pb_type_xml, "input", ioattrs)
        elif iodir == "output":
            ET.SubElement(pb_type_xml, "output", ioattrs)
        else:
            assert False

    modes = yj.modules_with_attr("ALTERNATIVE_TO", mod.name)

    if len(modes) > 0:
        for mode_mod in modes:
            mode_xml = ET.SubElement(pb_type_xml, "mode", {"name" : mode_mod.name})
            make_pb_content(mode_mod, mode_xml)
    else:
        make_pb_content(mod, pb_type_xml)

    return pb_type_xml

pb_type_xml = make_pb_type(tmod)

outfile = "pb_type.xml"
if "o" in args and args.o is not None:
    outfile = args.o

f = open(outfile, 'w')
f.write(ET.tostring(pb_type_xml, pretty_print=True).decode('utf-8'))
f.close()
