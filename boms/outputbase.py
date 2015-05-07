"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""
from utils import log
logger = log.get_logger(__name__, log.DEBUG)

import csv
from entitybase import EntityBase


class OutputElnBomDescriptor(object):
    def __init__(self, pcbname, cardfolder, configname, configurations, multiplier=1):
        self.pcbname = pcbname
        self.cardfolder = cardfolder
        self.configname = configname
        self.multiplier = multiplier
        self.configurations = configurations


class OutputBomLine(object):

    def __init__(self, comp, parent):
        assert isinstance(comp, EntityBase)
        self.ident = comp.ident
        self.refdeslist = []
        self.parent = parent

    def add(self, comp):
        assert isinstance(comp, EntityBase)
        if comp.ident == self.ident:
            self.refdeslist.append(comp.refdes)
        else:
            logger.error("Ident Mismatch")

    @property
    def quantity(self):
        return len(self.refdeslist) * self.parent.descriptor.multiplier


class OutputBom(object):

    def __init__(self, descriptor):
        """

        :type descriptor: outputbase.OutputElnBomDescriptor
        """
        self.lines = []
        self.descriptor = descriptor

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=False)
        for line in self.lines:
            line.refdeslist.sort()

    def find_by_ident(self, ident):
        for line in self.lines:
            assert isinstance(line, OutputBomLine)
            if line.ident == ident:
                return line
        return None

    def insert_component(self, item):
        assert isinstance(item, EntityBase)
        line = self.find_by_ident(item.ident)
        if line is None:
            line = OutputBomLine(item, self)
            self.lines.append(line)
        line.add(item)

    def multiply(self, factor, composite=False):
        if composite is True:
            self.descriptor.multiplier = self.descriptor.multiplier * factor
        else:
            self.descriptor.multiplier = factor


class CompositeOutputBomLine(object):

    def __init__(self, line, colcount):
        self.ident = line.ident
        self.columns = [0] * colcount

    def add(self, line, column):
        """

        :type line: outputbase.OutputBomLine
        """
        if line.ident == self.ident:
            self.columns[column] = line.quantity
        else:
            logger.error("Ident Mismatch")

    @property
    def quantity(self):
        return sum(self.columns)


class CompositeOutputBom():
    def __init__(self, bom_list):
        self.descriptors = []
        self.lines = []
        self.colcount = len(bom_list)
        i = 0
        for bom in bom_list:
            self.insert_bom(bom, i)
            i += 1
        self.sort_by_ident()

    def insert_bom(self, bom, i):
        """

        :type bom: outputbase.OutputBom
        """
        self.descriptors.append(bom.descriptor)
        for line in bom.lines:
            self.insert_line(line, i)

    def insert_line(self, line, i):
        """

        :type line: outputbase.OutputBomLine
        """
        cline = self.find_by_ident(line)
        if cline is None:
            cline = CompositeOutputBomLine(line, self.colcount)
            self.lines.append(cline)
        cline.add(line, i)

    def find_by_ident(self, line):
        """

        :type line: outputbase.OutputBomLine
        """
        for cline in self.lines:
            assert isinstance(cline, CompositeOutputBomLine)
            if cline.ident == line.ident:
                return cline
        return None

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=False)

    def dump(self, stream):
        writer = csv.writer(stream)
        writer.writerow(['device'] + [x.configname + ' x' + str(x.multiplier) for x in self.descriptors] + ['Total'])
        for line in self.lines:
            columns = [None if x == 0 else x for x in line.columns]
            writer.writerow([line.ident] + columns + [line.quantity])
