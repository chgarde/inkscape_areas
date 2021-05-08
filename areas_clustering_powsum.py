#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 

import inkex
from inkex import Group

class ClusteringPowerSum(inkex.EffectExtension):
    """
    this extension aims at facilitating identification / removal of elements with a similar area
    this is particularly usefull when converting bitmap to path as it generates a lot of small objects
    """

    def add_arguments(self, pars):
        """
        Arguments parsing
        """
        pars.add_argument("--max_clusters", type=int, default=10.0,\
            help="max clusters")
        pars.add_argument("--di", type=float, default=10.0,\
            help="initial delta in % of min area (di)")
        pars.add_argument("--f", type=float, default=2.5,\
            help="delta multiplication factor (f)")
        pars.add_argument("--k", type=float, default=2,\
            help="delta search factor (k)")

    
    def get_or_create_layer(self,layer_name):
        """
        get or create a layer
        """

        # Test if webslicer-layer layer existis
        layer = self.svg.getElement(
            '//*[@id="{}" and @inkscape:groupmode="layer"]'.format(layer_name))
        if layer is None:
            # Create a new layer
            layer = Group(id=layer_name)
            layer.set('inkscape:label', layer_name)
            layer.set('inkscape:groupmode', 'layer')
            self.document.getroot().append(layer)
        return layer

    
    def get_cluster_for_value(self,clusters,area):
        """
        find out in which cluster an area belongs
        """
        for c in clusters:
            if area>=c["min"] and area<=c["max"]:
                return c["name"]
        self.msg("Could not find cluster for {}".format(area))
        return clusters[0]["name"]

    # move object to layer
    def move_to_layer(self,node,layer):
        layer.add(node.copy())
        node.delete()

    def compute_clusters(self,n,mini,delta,f):
        """
        recursive build of the clusters.
        the clusters get larger and larger, by a factor of f
        cluster0 : width = delta0
        cluster1 : width = delta1 = delta0 * f
        cluster2 : width = delta2 = delta1 * f 
        cluster3 : width = delta3 = delta2 * f 
        etc...
        """

        if n>0:
            cluster_name="cluster{:0>2d}".format(n)
            max=mini+delta
            cluster=[{"name":cluster_name,"min": mini,"max": max}]
            cluster2=self.compute_clusters(n-1,max,delta*f,f)
            if cluster2 is None:
                return cluster
            else:
                return cluster+cluster2
        else:
            return None

    def effect(self):
        """
        Create layers and assign objects into them according to their respective areas.
        please note that the Compute Area extension must be called first to pre-assign areas to objects.
        """

        if not self.svg.selected:
            raise inkex.AbortExtension("Please select some objects first.")
        
        # build an array with all areas
        areas=[]
        for (i,node) in enumerate(self.svg.selection.filter(inkex.PathElement).values()):
              areas.append(float(node.get("data-area")))
        
        # sanity check
        if len(areas)==0:
            raise inkex.AbortExtension("You must call Area > Compute first before using this.")
        
        # compute min/max of areas    
        mini=min(areas)
        maxi=max(areas)

        ################################
        # compute initial delta
        ################################

        # we have to start somewhere... 10% of the min_area makes sense.
        delta=mini*self.options.di/100
        
        # thanks to http://mikestoolbox.com/powersum.html
        # here is the poor's man solution : iterating until we find a convenient value !
        while True:
            # compute the sum of the bucket widths
            m=mini+delta*(pow(self.options.f,self.options.max_clusters)-1)/(self.options.f-1)
            # check if it includes the biggest object
            if m<maxi:
                # if not, then we increase the initial delta by a factor of k
                delta=delta*self.options.k
            else:
                break
        
        self.msg("Optimal delta={}".format(delta))
        
        #################################
        # Assign clusters = layers
        #################################
        # now that we have delta0, lets compute a nice dict with the cluster name, min_area and max_area
        clusters=self.compute_clusters(self.options.max_clusters,mini,delta,self.options.f)
        
        # give some informative feedback
        # and create layers
        self.msg(":::Found clusters:::")
        for c in clusters:
            self.msg(c)
            self.get_or_create_layer(c["name"])

        # move the elements in the corresponding layer
        for (i,node) in enumerate(self.svg.selection.filter(inkex.PathElement).values()):
            cluster_name=self.get_cluster_for_value(clusters,float(node.get("data-area")))
            self.move_to_layer(node,self.get_or_create_layer(cluster_name))

        self.msg("Done!")
        return None

if __name__ == '__main__':
    ClusteringPowerSum().run()

