import re
from collections import namedtuple, defaultdict

Element = namedtuple('Element', 'loc type name ios')
Wire = namedtuple('Wire', 'srcloc name inverted')
VerilogIO = namedtuple('VerilogIO', 'name direction ioloc')


class VModule(object):
    '''Represents a Verilog module for QLAL4S3B FASM'''

    def __init__(
            self,
            vpr_tile_grid,
            belinversions,
            interfaces,
            designconnections,
            inversionpins,
            io_to_fbio,
            useinversionpins=True
    ):
        '''Prepares initial structures.

        Refer to fasm2bels.py for input description.
        '''

        self.vpr_tile_grid = vpr_tile_grid
        self.belinversions = belinversions
        self.interfaces = interfaces
        self.designconnections = designconnections
        self.inversionpins = inversionpins
        self.useinversionpins = useinversionpins
        self.io_to_fbio = io_to_fbio

        # dictionary holding inputs, outputs
        self.ios = {}
        # dictionary holding declared wires (wire value;)
        self.wires = {}
        # dictionary holding Verilog elements
        self.elements = defaultdict(dict)
        # dictionary holding assigns (assign key = value;)
        self.assigns = {}

        # helper representing last input id
        self.last_input_id = 0
        # helper representing last output id
        self.last_output_id = 0

        self.qlal4s3bmapping = {
            'LOGIC': 'logic_cell_macro',
            'ASSP': 'qlal4s3b_cell_macro',
            'inv': 'inv'
        }

    def group_array_values(self, parameters: dict):
        '''Groups pin names that represent array indices.

        Parameters
        ----------
        parameters: dict
            A dictionary holding original parameters

        Returns
        -------
        dict: parameters with grouped array indices
        '''
        newparameters = dict()
        arraydst = re.compile(
            r'(?P<varname>[a-zA-Z_][a-zA-Z_0-9$]+)\[(?P<arrindex>[0-9]+)\]'
        )
        for dst, src in parameters.items():
            match = arraydst.match(dst)
            if match:
                varname = match.group('varname')
                arrindex = int(match.group('arrindex'))
                if varname not in newparameters:
                    newparameters[varname] = {arrindex: src}
                else:
                    newparameters[varname][arrindex] = src
            else:
                newparameters[dst] = src
        return newparameters

    def form_verilog_element(self, loc, typ: str, name: str, parameters: dict):
        '''Creates an entry representing single Verilog submodule.

        Parameters
        ----------
        loc: Loc
            Cell coordinates
        typ: str
            Cell type
        name: str
            Name of the submodule
        parameters: dict
            Map from input pin to source wire

        Returns
        -------
        str: Verilog entry
        '''
        params = []
        moduletype = self.qlal4s3bmapping[typ]
        result = f'    {moduletype} {name} ('
        fixedparameters = self.group_array_values(parameters)
        for inpname, inp in fixedparameters.items():
            if isinstance(inp, dict):
                arr = []
                maxindex = max([val for val in inp.keys()])
                for i in range(maxindex + 1):
                    if i not in inp:
                        arr.append("1'b0")
                    else:
                        arr.append(inp[i])
                arrlist = ', '.join(arr)
                params.append(f'.{inpname}({{{arrlist}}})')
            else:
                params.append(f'.{inpname}({inp})')
        if self.useinversionpins:
            if typ in self.inversionpins:
                for toinvert, inversionpin in self.inversionpins[typ].items():
                    if toinvert in self.belinversions[loc][typ]:
                        params.append(f".{inversionpin}(1'b1)")
                    else:
                        params.append(f".{inversionpin}(1'b0)")

        result += f',\n{" " * len(result)}'.join(sorted(params)) + ');\n'
        return result

    @staticmethod
    def get_element_name(tile):
        '''Forms element name from its type and FASM feature name.'''
        return f'{tile.type}_{tile.name}'

    def new_io_name(self, direction):
        '''Creates a new IO name for a given direction.

        Parameters
        ----------
        direction: str
            Direction of the IO, can be 'input' or 'output'
        '''
        # TODO add support for inout
        assert direction in ['input', 'output']
        if direction == 'output':
            name = f'out_{self.last_output_id}'
            self.last_output_id += 1
        elif direction == 'input':
            name = f'in_{self.last_input_id}'
            self.last_input_id += 1
        else:
            pass
        return name

    def get_wire(self, loc, wire, inputname):
        '''Creates or gets an existing wire for a given source.

        Parameters
        ----------
        loc: Loc
            Location of the destination cell
        wire: tuple
            A tuple of location of the source cell and source pin name
        inputname: str
            A name of the destination pin

        Returns
        -------
        str: wire name
        '''
        isoutput = self.vpr_tile_grid[loc].type == 'SYN_IO'
        if isoutput:
            # outputs are never inverted
            inverted = False
        else:
            # determine if inverted
            inverted = (
                inputname in self.belinversions[loc][
                    self.vpr_tile_grid[loc].type]
            )
        wireid = Wire(wire[0], wire[1], inverted)
        if wireid in self.wires:
            # if wire already exists, use it
            return self.wires[wireid]

        # first create uninverted wire
        uninvertedwireid = Wire(wire[0], wire[1], False)
        if uninvertedwireid in self.wires:
            # if wire already exists, use it
            wirename = self.wires[uninvertedwireid]
        else:
            srcname = self.vpr_tile_grid[wire[0]].name
            srctype = self.vpr_tile_grid[wire[0]].type
            srconame = wire[1]
            if srctype == 'SYN_IO':
                # if source is input, use its name
                if wire[0] not in self.ios:
                    self.ios[wire[0]] = VerilogIO(
                        name=self.new_io_name('input'),
                        direction='input',
                        ioloc=wire[0]
                    )
                assert self.ios[wire[0]].direction == 'input'
                wirename = self.ios[wire[0]].name
            else:
                # form a new wire name
                wirename = f'{srcname}_{srconame}'
            if srctype not in self.elements[wire[0]]:
                # if the source element does not exist, create it
                self.elements[wire[0]][srctype] = Element(
                    wire[0], srctype,
                    self.get_element_name(self.vpr_tile_grid[wire[0]]),
                    {srconame: wirename}
                )
            else:
                # add wirename to the existing element
                self.elements[wire[0]][srctype].ios[srconame] = wirename
            if not isoutput and srctype != 'SYN_IO':
                # add wire
                self.wires[uninvertedwireid] = wirename
            elif isoutput:
                # add assign to output
                self.assigns[self.ios[loc].name] = wirename

        if not inverted or (
                self.useinversionpins and
                inputname in self.inversionpins[self.vpr_tile_grid[loc].type]):
            # if not inverted or we're not inverting, just finish
            return wirename

        # else create an inverted and wire for it
        invertername = f'{wirename}_inverter'

        invwirename = f'{wirename}_inv'

        inverterios = {'Q': invwirename, 'A': wirename}

        inverterelement = Element(wire[0], 'inv', invertername, inverterios)
        self.elements[wire[0]]['inv'] = inverterelement
        invertedwireid = Wire(wire[0], wire[1], True)
        self.wires[invertedwireid] = invwirename
        return invwirename

    def parse_bels(self):
        '''Converts BELs to Verilog-like structures.'''
        # TODO add support for direct input-to-output
        # first parse outputs to create wires for them

        # parse outputs first to properly handle namings
        for currloc, connections in self.designconnections.items():
            if self.vpr_tile_grid[currloc].type == 'SYN_IO':
                if 'OQI' in connections:
                    self.ios[currloc] = VerilogIO(
                        name=self.new_io_name('output'),
                        direction='output',
                        ioloc=currloc
                    )
                    self.get_wire(currloc, connections['OQI'], 'OQI')
                # TODO parse IE/INEN, check iz

        # process of BELs
        for currloc, connections in self.designconnections.items():
            # Extract type and form name for the BEL
            currtype = self.vpr_tile_grid[currloc].type
            currname = self.get_element_name(self.vpr_tile_grid[currloc])
            inputs = {}
            # form all inputs for the BEL
            for inputname, wire in connections.items():
                if wire[1] == 'VCC':
                    inputs[inputname] = "1'b1"
                    continue
                elif wire[1] == 'GND':
                    inputs[inputname] = "1'b0"
                    continue
                srctype = self.vpr_tile_grid[wire[0]].type
                if srctype in ['SYN_IO', 'LOGIC', 'ASSP']:
                    # FIXME handle already inverted pins
                    # TODO handle inouts
                    wirename = self.get_wire(currloc, wire, inputname)
                    inputs[inputname] = wirename
                else:
                    raise Exception('Not supported cell type')
            if currtype not in self.elements[currloc]:
                # If Element does not exist, create it
                self.elements[currloc][currtype] = Element(
                    currloc, currtype, currname, inputs
                )
            else:
                # else update IOs
                self.elements[currloc][currtype].ios.update(inputs)

    def generate_verilog(self):
        '''Creates Verilog module

        Returns
        -------
        str: A Verilog module for given BELs
        '''
        ios = ''
        wires = ''
        assigns = ''
        elements = ''

        if len(self.ios) > 0:
            sortedios = sorted(
                self.ios.values(), key=lambda x: (x.direction, x.name)
            )
            ios = '\n    '
            ios += ',\n    '.join(
                [f'{x.direction} {x.name}' for x in sortedios]
            )

        if len(self.wires) > 0:
            wires += '\n'
            for wire in self.wires.values():
                wires += f'    wire {wire};\n'

        if len(self.assigns) > 0:
            assigns += '\n'
            for dst, src in self.assigns.items():
                assigns += f'    assign {dst} = {src};\n'

        if len(self.elements) > 0:
            for eloc, locelements in self.elements.items():
                for element in locelements.values():
                    if element.type != 'SYN_IO':
                        elements += '\n'
                        elements += self.form_verilog_element(
                            eloc, element.type, element.name, element.ios
                        )

        verilog = (
            f'module top ({ios});\n'
            f'{wires}'
            f'{assigns}'
            f'{elements}'
            f'\n'
            f'endmodule'
        )
        return verilog

    def generate_pcf(self):
        pcf = ''
        for io in self.ios.values():
            pcf += f'set_io {io.name} {self.io_to_fbio[io.ioloc]}\n'
        return pcf

    def generate_qcf(self):
        qcf = '#[Fixed Pin Placement]\n'
        for io in self.ios.values():
            qcf += f'place {io.name} {self.io_to_fbio[io.ioloc]}\n'
        return qcf