# encoding: utf-8
from __future__ import division, print_function, unicode_literals

###########################################################################################################
#
#
#	Filter without dialog Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Filter%20without%20Dialog
#
#
###########################################################################################################

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

class MakeCorner(FilterWithoutDialog):
	
	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Make Corner',
			'de': u'Ecke herstellen',
			'es': u'Generar esquina',
			'fr': u'Générer coin',
		})
		self.keyboardShortcut = None # With Cmd+Shift
	
	@objc.python_method
	def intersection( self, pointA, pointB, pointC, pointD ):
		"""
		Returns an NSPoint of the intersection AB with CD.
		Or False if there is no intersection
		"""
		x1, y1 = pointA.x, pointA.y
		x2, y2 = pointB.x, pointB.y
		x3, y3 = pointC.x, pointC.y
		x4, y4 = pointD.x, pointD.y
		
		try:
			slope12 = ( float(y2) - float(y1) ) / ( float(x2) - float(x1) )
		except:
			slope12 = None # vertical
			
		try:
			slope34 = ( float(y4) - float(y3) ) / ( float(x4) - float(x3) )
		except:
			slope34 = None # vertical
		
		if slope12 == slope34:
			# parallel, no intersection
			return False
		elif slope12 is None:
			# first line is vertical
			x = x1
			y = slope34 * ( x - x3 ) + y3
		elif slope34 is None:
			# second line is vertical
			x = x3
			y = slope12 * ( x - x1 ) + y1
		else:
			# both lines have an angle
			x = ( slope12 * x1 - y1 - slope34 * x3 + y3 ) / ( slope12 - slope34 )
			y = slope12 * ( x - x1 ) + y1

		return NSPoint( x, y )

	@objc.python_method
	def filter(self, Layer, inEditView, customParameters):
		selection = Layer.selection
		
		selectionCounts = False
		if inEditView and selection:
			selectionCounts = True
		
		ghostLayer = GSLayer()
		
		for thisPath in Layer.paths:
			ghostPath = GSPath()
			numOfNodes = len(thisPath.nodes)

			for thisNodeIndex in range(numOfNodes):
				thisNode = thisPath.nodes[ thisNodeIndex ]
				prevNode = thisPath.nodes[ (thisNodeIndex - 1) % numOfNodes ]
				
				if thisNode.type == GSOFFCURVE:
					if prevNode.type != GSOFFCURVE:
						nextNode = thisPath.nodes[ thisNodeIndex + 1 ]
						bothNodesAreOffcurve = (thisNode.type == GSOFFCURVE) and (nextNode.type == GSOFFCURVE)
					
						if bothNodesAreOffcurve:
							thisNodeCounts = thisNode in selection or not selectionCounts
							nextNodeCounts = nextNode in selection or not selectionCounts
							nodeAfterNextNode = thisPath.nodes[ (thisNodeIndex + 2) % numOfNodes ]
						
							if thisNodeCounts or nextNodeCounts:
								# make corner out of thisNode and nextNode
								cornerPoint = self.intersection( prevNode.position, thisNode.position, nextNode.position, nodeAfterNextNode.position )

								if cornerPoint:
									cornerNode = GSNode()
									cornerNode.position = cornerPoint
									cornerNode.type = GSLINE
									cornerNode.connection = GSSHARP
									ghostPath.nodes.append( cornerNode )
									
									linePoint = nodeAfterNextNode.copy()
									linePoint.type = GSLINE
									ghostPath.nodes.append( linePoint )
								else:
									# add both offcurves as they are:
									ghostPath.nodes.append( thisNode.copy() )
									ghostPath.nodes.append( nextNode.copy() )
									ghostPath.nodes.append( nodeAfterNextNode.copy() )
							else:
								# add both offcurves as they are:
								ghostPath.nodes.append( thisNode.copy() )
								ghostPath.nodes.append( nextNode.copy() )
								ghostPath.nodes.append( nodeAfterNextNode.copy() )
						else:
							# do not make corner, keep the point as it is:
							ghostPath.nodes.append( thisNode.copy() )
							
				elif thisNode.type != GSCURVE:
					# keep the on-curve point as it is:
					ghostPath.nodes.append( thisNode.copy() )
			
			ghostPath.closed = True
			try:
				ghostLayer.shapes.append( ghostPath )
			except:
				ghostLayer.paths.append( ghostPath )
		
		Layer.paths = ghostLayer.paths
		if selectionCounts:
			Layer.selection = None
	
	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
	