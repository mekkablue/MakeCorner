#!/usr/bin/env python
# encoding: utf-8

import objc
from Foundation import *
from AppKit import *
import sys, os, re

MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append( path )

import GlyphsApp
from GlyphsApp import GSMOVE, GSLINE, GSCURVE, GSOFFCURVE, GSSHARP, GSSMOOTH

GlyphsFilterProtocol = objc.protocolNamed( "GlyphsFilter" )

class GlyphsFilterMakeCorner ( NSObject, GlyphsFilterProtocol ):

	def init( self ):
		"""
		Do all initializing here.
		"""
		try:
			return self
		except Exception as e:
			self.logToConsole( "init: %s" % str(e) )
	
	def interfaceVersion( self ):
		"""
		Distinguishes the API version the plugin was built for. 
		Return 1.
		"""
		try:
			return 1
		except Exception as e:
			self.logToConsole( "interfaceVersion: %s" % str(e) )
	
	def title( self ):
		"""
		This is the human-readable name as it appears in the Filter menu.
		"""
		try:
			return "Make Corner"
		except Exception as e:
			self.logToConsole( "title: %s" % str(e) )
	
	def setController_( self, Controller ):
		"""
		Sets the controller, you can access it with controller().
		Do not touch this.
		"""
		try:
			self._controller = Controller
		except Exception as e:
			self.logToConsole( "setController_: %s" % str(e) )
	
	def controller( self ):
		"""
		Do not touch this.
		"""
		try:
			return self._controller
		except Exception as e:
			self.logToConsole( "controller: %s" % str(e) )
		
	def setup( self ):
		"""
		Do not touch this.
		"""
		try:
			return None
		except Exception as e:
			self.logToConsole( "setup: %s" % str(e) )
	
	def keyEquivalent( self ):
		""" 
		The key together with Cmd+Shift will be the shortcut for the filter.
		Return None if you do not want to set a shortcut.
		Users can set their own shortcuts in System Prefs.
		"""
		try:
			return None
		except Exception as e:
			self.logToConsole( "keyEquivalent: %s" % str(e) )
	
	def intersection( self, pointA, pointB, pointC, pointD ):
		"""
		Returns an NSPoint of the intersection AB with CD.
		Or False if there is no intersection
		"""
		try:
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
			
		except Exception as e:
			self.logToConsole( "intersection: %s" % str(e) )
			return False
	
	def processLayer( self, Layer, selectionCounts ):
		"""
		Each layer is eventually processed here. This is where your code goes.
		If selectionCounts is True, then apply the code only to the selection.
		"""
		try:
			try:
				# until v2.1:
				selection = Layer.selection()
			except:
				# since v2.2:
				selection = Layer.selection
				
			if selectionCounts == True:
				if selection == (): # empty selection
					selectionCounts = False
			
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
				ghostLayer.paths.append( ghostPath )
			
			Layer.setPaths_( None )
			
			for thisPath in ghostLayer.paths:
				Layer.addPath_( thisPath )
				
			return ( True, None )
		except Exception as e:
			self.logToConsole( "processLayer: %s" % str(e) )
			return ( False, None )
	
	def runFilterWithLayers_error_( self, Layers, Error ):
		"""
		Invoked when user triggers the filter through the Filter menu
		and more than one layer is selected.
		"""
		try:
			for k in range(len(Layers)):
				Layer = Layers[k]
				Layer.clearSelection()
				self.processLayer( Layer, False ) # ignore selection
		except Exception as e:
			self.logToConsole( "runFilterWithLayers_error_: %s" % str(e) )
	
	def runFilterWithLayer_options_error_( self, Layer, Options, Error ):
		"""
		Required for compatibility with Glyphs version 702 or later.
		Leave this as it is.
		"""
		try:
			return self.runFilterWithLayer_error_( self, Layer, Error )
		except Exception as e:
			self.logToConsole( "runFilterWithLayer_options_error_: %s" % str(e) )
	
	def runFilterWithLayer_error_( self, Layer, Error ):
		"""
		Invoked when user triggers the filter through the Filter menu
		and only one layer is selected.
		"""
		try:
			return self.processLayer( Layer, True ) # respect selection
		except Exception as e:
			self.logToConsole( "runFilterWithLayer_error_: %s" % str(e) )
			return False
	
	def processFont_withArguments_( self, Font, Arguments ):
		"""
		Invoked when called as Custom Parameter in an instance at export.
		The Arguments come from the custom parameter in the instance settings. 
		Item 0 in Arguments is the class-name. The consecutive items should be your filter options.
		"""
		try:
			# set glyphList to all glyphs
			glyphList = Font.glyphs
			
			# Override defaults with actual values from custom parameter:
			if len( Arguments ) > 1:
				
				# change glyphList to include or exclude glyphs
				if "exclude:" in Arguments[-1]:
					excludeList = [ n.strip() for n in Arguments.pop(-1).replace("exclude:","").strip().split(",") ]
					glyphList = [ g for g in glyphList if not g.name in excludeList ]
				elif "include:" in Arguments[-1]:
					includeList = [ n.strip() for n in Arguments.pop(-1).replace("include:","").strip().split(",") ]
					glyphList = [ Font.glyphs[n] for n in includeList ]
			
			FontMasterId = Font.fontMasterAtIndex_(0).id
			for thisGlyph in glyphList:
				Layer = thisGlyph.layerForKey_( FontMasterId )
				self.processLayer( Layer, False )
		except Exception as e:
			self.logToConsole( "processFont_withArguments_: %s" % str(e) )
	
	def logToConsole( self, message ):
		"""
		The variable 'message' will be passed to Console.app.
		Use self.logToConsole( "bla bla" ) for debugging.
		"""
		myLog = "Filter %s:\n%s" % ( self.title(), message )
		print myLog
		NSLog( myLog )
