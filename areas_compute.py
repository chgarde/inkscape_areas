#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 

import inkex
from inkex.bezier import csparea

class ComputeAreasEffect(inkex.EffectExtension):
    """
    this extension will compute all areas and set the tag data-area on each element.
    it then permits to re-use areas in other extensions
    """

    def compute_areas(self):
        """
        compute areas of the selected objects
        and set the tag data-area on each element.
        """

        for node in self.svg.selection.filter(inkex.PathElement).values():
            csp = node.path.transform(node.composed_transform()).to_superpath()
            area = round(abs(csparea(csp)))
            # SVG2 allows custom attributes starting with data-
            node.set("data-area",area)

    """Show document information"""
    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object")
        self.compute_areas()
        return None

if __name__ == '__main__':
    ComputeAreasEffect().run()
