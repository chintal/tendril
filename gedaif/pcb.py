"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os
import subprocess
import pyparsing

import utils.pdf

from utils.types.lengths import Length


class StringFlags(object):
    """
        From :
        PCB file parser written by Lilith Byrant 2014
        http://pastebin.com/2TqbDfKf
        GPLv2
    """
    L = pyparsing.Literal("(").suppress()
    R = pyparsing.Literal(")").suppress()
    PartStart = pyparsing.Regex(r"[^,\(\)]*")
    CSV = pyparsing.delimitedList(PartStart)
    Part = pyparsing.Group(PartStart + pyparsing.Group(pyparsing.Optional(L + CSV + R)))
    Parts = pyparsing.delimitedList(Part)

    def __init__(self, s):
        self.s = s
        all_flags = StringFlags.Parts.parseString(s)
        self.flags = set([PP[0] for PP in all_flags if PP[0] != "thermal"])
        thermal_flags = [PP for PP in all_flags if PP[0] == "thermal"]
        if len(thermal_flags) == 0:
            self.thermals = {}
        else:
            t = set(thermal_flags[0][1])
            self.thermals = dict([(i[0], (i+"!")[1]) for i in t])

    def __contains__(self, s):
        if s == "thermal":
            return len(self.thermals) > 0
        else:
            return s in self.flags

    def add(self, s):
        self.flags.add(s)

    def remove(self, s):
        if s in self.flags:
            self.flags.remove(s)

    def add_thermal(self, n, ttype):
        self.thermals[n] = ttype

    def remove_thermal(self, n):
        if n in self.thermals:
            del self.thermals[n]

    def remove_all_thermal(self):
        self.thermals = {}

    def __str__(self):
        if self.thermals is not None and len(self.thermals) > 0:
            s = [str(i[0])+(str(i[1]).replace("!", "")) for i in self.thermals.items()]
            t = "thermal("+",".join(sorted(s))+")"
            return ",".join(list(self.flags) + [t])
        else:
            return ",".join(self.flags)

    def __repr__(self):
        return self.__str__()


def length(s, loc, toks):
    if toks is not None and len(toks):
        try:
            toks = [Length(lstr=token, defunit='cmil') for token in toks]
        except Exception, e:
            print "Exception : ", loc, toks
            raise e
        return toks
    else:
        print s


def build_bnf(pp=pyparsing):
    """
        From :
        PCB file parser written by Lilith Byrant 2014
        http://pastebin.com/2TqbDfKf
        GPLv2
    """
    S = pp.Suppress
    C = pp.Combine
    G = pp.Group

    LRND = S(pp.Literal("("))
    RRND = S(pp.Literal(")"))
    LSQ = S(pp.Literal("["))
    RSQ = S(pp.Literal("]"))

    Str = pp.QuotedString('"')
    Char = pp.Regex(r"'.'")

    Meas = pp.Regex(r"-?[0-9\\.]+[a-z]*")
    Meas.addParseAction(length)

    Digits = pp.Regex(r"-?[0-9]+")
    Digits.setParseAction(lambda t: int(t[0]))

    Float = pp.Regex(r"-?[0-9\\.]+")
    Float.setParseAction(lambda t: float(t[0]))

    Comment = pp.Literal('#') + pp.restOfLine

    SFlags = C(Str)
    SFlags.setParseAction(lambda t: StringFlags(t[0]))

    QSFlags = SFlags

    FileVersion = pp.Keyword("FileVersion") + LSQ + Digits("Version") + RSQ
    PCB = pp.Keyword("PCB") + LSQ + (Str("Name") + Meas("Width") + Meas("Height"))("PCB") + RSQ
    Grid = pp.Keyword("Grid") + LSQ+Meas("Step") + Meas("OffsetX") + Meas("OffsetY") + Digits("Visible") + RSQ
    PolyArea = pp.Keyword("PolyArea") + LSQ+Float("Area") + RSQ
    Thermal = pp.Keyword("Thermal") + LSQ+Float("Scale") + RSQ
    DRC = pp.Keyword("DRC") + LSQ + Meas("Bloat") + Meas("Shrink") + \
        Meas("Line") + Meas("Silk") + Meas("Drill") + Meas("Ring") + RSQ
    Flags = pp.Keyword("Flags") + LRND + QSFlags("Flags") + RRND
    Groups = pp.Keyword("Groups") + LRND + Str("Groups") + RRND
    Styles = pp.Keyword("Styles") + LSQ + Str("Styles") + RSQ
    Mark = pp.Keyword("Mark") + LSQ + Meas("X")+Meas("Y") + RSQ
    Cursor = pp.Keyword("Cursor") + LSQ + Meas("X") + Meas("Y") + Float("Zoom") + RSQ

    PCBAttribute = pp.Keyword("Attribute") + LRND + Str("AttrKey") + Str("AttrValue") + RRND
    SymbolLine = pp.Keyword("SymbolLine") + LSQ + Meas("X1") + Meas("Y1") + \
        Meas("X2") + Meas("Y2") + Meas("Thickness") + RSQ

    SymContent2 = SymbolLine
    SymContent = G(SymContent2)
    SymContent = SymContent.setResultsName("Content", True)

    PCBSymbol = pp.Keyword("Symbol") + LSQ + Char("Char") + Meas("Delta") + RSQ + \
        LRND + pp.ZeroOrMore(SymContent) + RRND

    Via = pp.Keyword("Via") + LSQ + Meas("X") + Meas("Y") + Meas("Thickness") + \
        Meas("Clearance") + Meas("Mask") + Meas("Drill") + Str("Name") + QSFlags("SFlags") + RSQ
    Pin = pp.Keyword("Pin") + LSQ + Meas("rX") + Meas("rY") + Meas("Thickness") + \
        Meas("Clearance") + Meas("Mask") + Meas("Drill") + Str("Name") + Str("Number") + QSFlags("SFlags") + RSQ
    Pad = pp.Keyword("Pad") + LSQ + Meas("rX1") + Meas("rY1") + Meas("rX2") + Meas("rY2") + Meas("Thickness") + \
        Meas("Clearance") + Meas("Mask") + Str("Name") + Str("Number") + QSFlags("SFlags") + RSQ

    ElementArc = pp.Keyword("ElementArc") + LSQ + Meas("X") + Meas("Y") + Meas("Width") + Meas("Height") + \
        Digits("StartAngle") + Digits("DeltaAngle") + Meas("Thickness") + RSQ
    ElementLine = pp.Keyword("ElementLine") + LSQ + Meas("X1") + Meas("Y1") + Meas("X2") + Meas("Y2") + \
        Meas("Thickness") + RSQ

    ElemContent2 = PCBAttribute | Pin | Pad | ElementLine | ElementArc
    ElemContent = G(ElemContent2)
    ElemContent = ElemContent.setResultsName("Content", True)

    PCBElement = (pp.Keyword("Element") + LSQ + QSFlags("SFlags") + Str("Desc") + Str("Name") + Str("Value") +
                  Meas("MX") + Meas("MY") + Meas("TX") + Meas("TY") + Digits("TDir") + Digits("TScale") +
                  QSFlags("TSFlags") + RSQ + LRND + pp.ZeroOrMore(ElemContent) + RRND)

    Rat = pp.Keyword("Rat") + LSQ + Meas("X1") + Meas("Y1") + Digits("Group1") + Meas("X2") + Meas("Y2") + \
        Digits("Group2") + QSFlags("SFlags") + RSQ
    Line = pp.Keyword("Line") + LSQ + Meas("X1") + Meas("Y1") + Meas("X2") + Meas("Y2") + Meas("Thickness") + \
        Meas("Clearance") + QSFlags("SFlags") + RSQ
    Arc = pp.Keyword("Arc") + LSQ + Meas("X") + Meas("Y") + Meas("Width") + Meas("Height") + Meas("Thickness") + \
        Meas("Clearance") + Digits("StartAngle") + Digits("DeltaAngle") + QSFlags("SFlags") + RSQ
    Text = pp.Keyword("Text") + LSQ + Meas("X") + Meas("Y") + Digits("Direction") + Meas("Scale") + Str("String") + \
        QSFlags("SFlags") + RSQ

    PolyVertex = LSQ + Meas("X") + Meas("Y") + RSQ
    PolyVertex = PolyVertex.setResultsName("Vertex", True)

    Hole = pp.Keyword("Hole") + LRND + pp.ZeroOrMore(PolyVertex) + RRND

    PolyContent2 = PolyVertex | Hole
    PolyContent = G(PolyContent2)
    PolyContent = PolyContent.setResultsName("Content", True)

    Polygon = pp.Keyword("Polygon") + LRND + QSFlags("SFlags") + RRND + LRND + pp.ZeroOrMore(PolyContent) + RRND

    LayerContent2 = PCBAttribute | Line | Arc | Polygon | Text
    LayerContent = G(LayerContent2)
    LayerContent = LayerContent.setResultsName("Content", True)

    Layer = pp.Keyword("Layer") + LRND + Digits("LayerNum") + Str("Name") + RRND + \
        LRND + pp.ZeroOrMore(LayerContent) + RRND

    Connect = pp.Keyword("Connect") + LRND + Str("PinPad") + RRND
    Connect = Connect.setResultsName("Connect", True)

    Net = pp.Keyword("Net") + LRND + Str("Name") + Str("Style") + RRND + \
        LRND + pp.ZeroOrMore(Connect) + RRND
    Net = Net.setResultsName("Net", True)

    NetList = pp.Keyword("NetList") + LRND + RRND + \
        LRND + pp.ZeroOrMore(Net) + RRND

    TopLevelThing2 = Comment | FileVersion | PCB | Grid | PolyArea | Thermal | DRC | Flags | Groups | Styles | \
        Mark | Cursor | PCBSymbol | PCBAttribute | Via | PCBElement | Rat | Layer | NetList

    TopLevelThing = G(TopLevelThing2)
    TopLevelThing = TopLevelThing.setResultsName("Content", True)

    FileGrammar = pp.ZeroOrMore(TopLevelThing)

    return FileGrammar


def conv_pcb2pdf(pcbpath, docfolder, projname):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    psfile = os.path.join(docfolder, projname + '-pcb.ps')
    subprocess.call(['pcb', '-x', 'ps',
                     '--psfile', psfile,
                     '--outline', '--media', 'A4', '--show-legend',
                     pcb_file], cwd=pcb_folder)
    pdffile = os.path.join(docfolder, projname + '-pcb.pdf')
    utils.pdf.conv_ps2pdf(psfile, pdffile)
    os.remove(psfile)
    return pdffile


def conv_pcb2gbr(pcbpath):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    gbrfile = os.path.join(os.path.join(pcb_folder, os.pardir), 'gerber', os.path.splitext(pcb_file)[0])
    subprocess.call(['pcb', '-x', 'gerber',
                     '--gerberfile', gbrfile,
                     '--all-layers', '--verbose', '--outline',
                     pcb_file], cwd=pcb_folder)
    return os.path.join(os.path.join(pcb_folder, os.pardir), 'gerber')


def conv_pcb2dxf(pcbpath, pcbname):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    dxffile = os.path.splitext(pcbpath)[0] + '.dxf'
    psfile = os.path.splitext(pcbpath)[0] + '.ps'
    subprocess.call(['pcb', '-x', 'ps',
                     '--psfile', psfile,
                     '--media', 'A4', '--show-legend', '--multi-file',
                     pcb_file], cwd=pcb_folder)
    psfile = os.path.splitext(pcbpath)[0] + '.top.ps'
    subprocess.call(['pstoedit', '-f', 'dxf', psfile, dxffile])
    cleanlist = [f for f in os.listdir(pcb_folder) if f.endswith(".ps")]
    for f in cleanlist:
        os.remove(os.path.join(pcb_folder, f))
    return dxffile
