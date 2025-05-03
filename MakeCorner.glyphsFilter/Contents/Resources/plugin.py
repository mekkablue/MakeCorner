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
from AppKit import NSPoint


class MakeCorner(FilterWithoutDialog):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': 'Make Corner',
			'de': 'Ecke wiederherstellen',
			'es': 'Regenerar esquina',
			'fr': 'Regénérer coin',
			'pt': 'Regenerar canto',
		})
		self.keyboardShortcut = None  # With Cmd+Shift


	@objc.python_method
	def intersection(self, pointA, pointB, pointC, pointD):
		"""
		Returns an NSPoint of the intersection AB with CD.
		Or False if there is no intersection
		"""
		x1, y1 = pointA.x, pointA.y
		x2, y2 = pointB.x, pointB.y
		x3, y3 = pointC.x, pointC.y
		x4, y4 = pointD.x, pointD.y

		try:
			slope12 = (float(y2) - float(y1)) / (float(x2) - float(x1))
		except:
			slope12 = None  # vertical

		try:
			slope34 = (float(y4) - float(y3)) / (float(x4) - float(x3))
		except:
			slope34 = None  # vertical

		if slope12 == slope34:
			# parallel, no intersection
			return False
		elif slope12 is None:
			# first line is vertical
			x = x1
			y = slope34 * (x - x3) + y3
		elif slope34 is None:
			# second line is vertical
			x = x3
			y = slope12 * (x - x1) + y1
		else:
			# both lines have an angle
			x = (slope12 * x1 - y1 - slope34 * x3 + y3) / (slope12 - slope34)
			y = slope12 * (x - x1) + y1

		return NSPoint(x, y)


	@objc.python_method
	def filter(self, layer, inEditView, customParameters):
		try:
			# determine the size threshold
			threshold = None
			glyph = layer.parent
			if glyph:
				font = glyph.parent
				if font:
					threshold = font.customParameterForKey_("Make Corner Threshold")
					if threshold is not None and threshold.active:
					try:
						threshold = int(threshold.value)
					except:
						pass

			selectionMatters = inEditView and layer.selection
			changesMade = False
			for shape in layer.shapes:

				# check on paths, ignor components
				if not isinstance(shape, GSPath):
					continue
					
				# only if they have enough points
				if len(shape.nodes) < 5:
					continue
				
				# step through all nodes
				for i in range(len(shape.nodes)-1, -1, -1):
					
					# check on the current node quadruplet
					A = shape.nodes[i]
					if A.type == OFFCURVE:
						continue
					B = A.nextNode
					if B.type != OFFCURVE:
						continue
					C = B.nextNode
					if C.type != OFFCURVE:
						continue
					D = C.nextNode
					if D.type == OFFCURVE:
						continue

					# check if we exceed threshold
					if threshold is None or abs(D.x-A.x) > threshold or abs(D.y-A.y) > threshold:
						continue

					# delete the remaining points if we are surrounded by line segments
					canDeleteA = A.prevNode.type != OFFCURVE
					canDeleteD = D.nextNode.type != OFFCURVE
					selected = B.selected or C.selected
					if not selected and selectionMatters:
						continue

					# create corner node
					cornerPosition = self.intersection(A, B, C, D)
					if not cornerPosition:
						continue
					corner = GSNode(cornerPosition, type=LINE)
					changesMade = True

					# rebuild the corner
					if canDeleteD:
						del shape.nodes[D.index]
					else:
						D.type = LINE
					del shape.nodes[C.index]
					del shape.nodes[B.index]
					shape.nodes.insert(A.index+1, corner)
					if canDeleteA:
						del shape.nodes[A.index]

			if changesMade:
				layer.clearSelection()

		except Exception as e:
			print(e)
			import traceback
			print(traceback.format_exc())

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
