#!/usr/bin/env python
"""
This script is intended to modify the XML architecture description file
in order to add the tile tags, necessary after the addition of the `tiles`
parsing capabilities of Verilog-to-Routing.

This script needs to be used only if the architecture import scripts do not
take into account the physical tiles tags. In fact, it is used as last step
of the architecture description generation.

It moves the top level pb_types attributes and tags to the tiles high-level tag.

BEFORE:
<complexblocklist>
    <pb_type name="BRAM" area="2" height="4" width="1" capacity="1">
        <inputs ... />
        <outputs ... />
        <interconnect ... />
        <fc ... />
        <pinlocations ... />
        <switchblock_locations ... />
    </pb_type>
</complexblocklist>

AFTER:
<tiles>
    <tile name="BRAM" area="2" height="4" width="1" capacity="1">
        <inputs ... />
        <outputs ... />
        <fc ... />
        <pinlocations ... />
        <switchblock_locations ... />
        <equivalent_sites>
            <site pb_type="BRAM"/>
        </equivalent_sites>
    </tile>
</tiles>
<complexblocklist
    <pb_type name="BRAM">
        <inputs ... />
        <outputs ... />
        <interconnect ... />
    </pb_type>
</complexblocklist>
"""

import argparse
import sys
import copy

from lxml import etree as ET


def add_tile_tags(arch):
    TAGS_TO_SWAP = ['fc', 'pinlocations', 'switchblock_locations']
    TAGS_TO_COPY = ['input', 'output', 'clock']
    ATTR_TO_SWAP = ['area', 'height', 'width', 'capacity']

    # A map of attribute names which have to be renamed.
    ATTR_MAP = {
        'num_pb': 'capacity'
    }

    def swap_tags(tile, pb_type):
        # Moving tags from top level pb_type to tile
        for child in pb_type:
            if child.tag in TAGS_TO_SWAP:
                pb_type.remove(child)
                tile.append(child)
            if child.tag in TAGS_TO_COPY:
                child_copy = copy.deepcopy(child)
                tile.append(child_copy)

    if arch.findall('./tiles'):
        return False

    models = arch.find('./models')

    tiles = ET.Element('tiles')
    models.addnext(tiles)

    top_pb_types = []
    for pb_type in arch.iter('pb_type'):
        if pb_type.getparent().tag == 'complexblocklist':
            top_pb_types.append(pb_type)

    for pb_type in top_pb_types:
        tile = ET.SubElement(tiles, 'tile')
        attrs = pb_type.attrib

        for attr in attrs:
            if attr in ATTR_MAP:
                tile.set(ATTR_MAP[attr], pb_type.get(attr))
            else:
                tile.set(attr, pb_type.get(attr))

        # Remove attributes of top level pb_types only
        for attr in ATTR_TO_SWAP:
            pb_type.attrib.pop(attr, None)
        for attr in ATTR_MAP.keys():
            pb_type.attrib.pop(attr, None)

        equivalent_sites = ET.Element("equivalent_sites")
        site = ET.Element("site")
        site.set("pb_type", attrs['name'])

        equivalent_sites.append(site)
        tile.append(equivalent_sites)

        swap_tags(tile, pb_type)

    return True


def add_site_directs(arch):
    TAGS_TO_COPY = ['input', 'output', 'clock']

    def add_directs(equivalent_site, pb_type):
        for child in pb_type:
            if child.tag in TAGS_TO_COPY:
                tile_name = equivalent_site.attrib['pb_type']
                port = child.attrib['name']

                from_to = "%s.%s" % (tile_name, port)

                direct = ET.Element("direct")
                direct.set("from", from_to)
                direct.set("to", from_to)
                equivalent_site.append(direct)

    if arch.findall('./tiles/tile/equivalent_sites/site/direct'):
        return False

    top_pb_types = []
    for pb_type in arch.iter('pb_type'):
        if pb_type.getparent().tag == 'complexblocklist':
            top_pb_types.append(pb_type)

    sites = []
    for pb_type in arch.iter('site'):
        sites.append(pb_type)

    for pb_type in top_pb_types:
        for site in sites:
            if pb_type.attrib['name'] == site.attrib['pb_type']:
                add_directs(site, pb_type)

    return True


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--in_xml", required=True, help="xml_file to update")
    parser.add_argument("--out_xml", required=True, help="updated xml_file")

    args = parser.parse_args()

    parser = ET.XMLParser(remove_blank_text=True)
    root = ET.parse(args.in_xml, parser)

    root_tags = root.findall(".")
    assert len(root_tags) == 1
    arch = root_tags[0]

    if arch.tag != "architecture":
        print("Warning! Not an architecture file, exiting...")
        sys.exit(0)

    modified = False
    result = add_tile_tags(arch)
    result = add_site_directs(arch)

    if result:
        modified = True

    if modified:
        with open(args.out_xml, "wb") as f:
            root.write(f, pretty_print=True)


if __name__ == "__main__":
    main()
