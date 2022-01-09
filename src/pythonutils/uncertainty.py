"""Module for performing calculations involving experimentally gathered values.

Important classes:
- CoherentUncertainty : value+-uncertainty objects, assuming the uncertainties
  are coherent
- IncoherentUncertainty : value+-uncertainty objects, not assuming the
  uncertainties are coherent
- FileHandler : load in .csv files with appropriate format to perform repeated
  calculations for many trials

General definitions (I really need to standardise these):
- "measurement": value+-unc      (Sometimes represented by an uppercase and
  lowercase of a letter: Aa, or A+-a)
- "value": the numerical estimate of a measurement (Represented by an uppercase
  letter: A)
- "uncertainty": the uncertainty in the measuremen (Represented by a lowercase
  letter: a)

Referennces:
- 

Things to look at:
- https://realpython.com/introduction-to-python-generators/
- https://www.python.org/dev/peps/pep-0396/ -- Specifying __version__
- PEP 563: Postponed Evaluation of Annotations -- type hints (hint of parameter
  classes to a function, and also of its return value)

Planned features:
- 

Miscealleneous:
- What I could do (if anyone who doesn't have python, or even knows how to code
  wants this) is make a javascript version where the html page they open has
  instructions on how to open the console, then examples on how to do the 
  calculations
- note: to start a python file in Visual Studio use shift+alt+F5

Improvements (general code efficiency/style)
- in CoherentUncertainty raise a warning if it detects incoherent uncertainties
- standardise how errors are raised!!!

- **Rename e.g. CoherentUncertainty to CoherentMeasurement to keep things
  standardised**
"""

__version__ = '0.2.2'
__author__ = "Nathan O'Neill"



################################### MODULES ###################################
from pythonutils import assorted as asd
import csv
import math
import numpy as np
import os
import pandas as pd



################################### CLASSES ###################################
class _Uncertainty_Prototype:
	"""Base class for uncertainties as approximated by 'Propagation of
	Uncertainty'.

	Notes
	-----
	`__myattribute` attributes should be removed from this documentation. If
	they're necessary, they should be protected properties instead of just 
	mentioning these!!!

	Attributes
	----------
	__prefixes : dict
		A dictionary of `prefix:powerOfTen` mappings. (This probably shouldn't
		be included).
	__autoOutputPrefix : bool
		Automatically display values with prefixes or not.
	
	"""

	## CLASSMETHODS ##
	__prefixes = {'p':10**(-12), 'n':10**(-9), 'u':10**(-6), 'm':10**(-3),
				  'c':10**(-2), '':1,'k':10**3, 'M':10**6, 'G':10**9, 'T':10**12}
	
	@classmethod
	def prefixToScale(cls, prefix):
		"""Return the number equivalent of a metric unit prefix
		
		Parameters
		----------
		prefix : str, int, float
			The prefix to be converted (`str`). If `int` or `float`,
			`prefixToScale` will return `prefix`
		
		Returns
		-------
		int, float
			The numerical equivalent of the prefix

		"""
		if isinstance(prefix, (int, float)):
			return prefix
		if not isinstance(prefix, str): 
			raise TypeError("prefix must be a string, int, or float, not '{}'".format(type(prefix)))

		if cls.isValidPrefix(prefix):
			return cls.__prefixes[prefix]
		else:
			raise KeyError("'{}' is not a valid prefix".format(prefix))
	
	@classmethod
	def addPrefix(cls, prefix, scale):
		"""Add a custom prefix.

		NOT IMPLEMENTED. Add a custom <prefix> that is interpreted numerically
		as <scale>. must be a positive number that is a multiple of 10.

		Thinking more on this, I believe there should be no restrictions (other
		than being real) that should be placed on `scale`.

		Parameters
		----------
		prefix : str
			Prefix to be added to memory.
		scale : int, float
			The numerical equivalent of `prefix`

		"""
		raise NotImplementedError
		if type(prefix) != str:
			raise TypeError("prefix must be a string, not '{}'".format(type(prefix)))
		if type(scale) not in [int, float]:
			raise TypeError("val must be a real number, not '{}'".format(type(scale)))
		if prefix in ['p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T']:
			raise ValueError("prefix '{}' cannot be one of the standard prefixes 'p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T'".format(prefix))
		if scale <= 0:
			raise ValueError("scale '{}' cannot be negative".format(scale))
		if scale % 10 != 0:  #+++ math.log(scale,10) != 0 instead?
			raise ValueError("scale '{}' must be a multiple of 10".format(scale))
		cls.__prefixes[prefix] = scale
	
	@classmethod
	def removePrefix(cls, prefix):
		"""Remove a custom `prefix`.

		Parameters
		----------
		prefix : str
			Prefix to be removed.
		
		"""
		raise NotImplementedError
		if type(prefix) != str:
			raise TypeError("prefix must be a string, not " + str(type(prefix)))
		if prefix in ['p', 'n', 'u', 'm', 'c', 'd', 'da', 'h', 'k', 'M', 'G', 'T']:
			raise ValueError("prefix '{}' cannot be one of the standard prefixes 'p', 'n', 'u', 'm', 'c', 'd', 'da', 'h', 'k', 'M', 'G', 'T'".format(prefix))
		del cls.__prefixes[prefix]
	
	@classmethod
	def isValidPrefix(cls, prefix):
		"""Return if a prefix is valid.

		Parameters
		----------
		prefix : str
			Prefix to check
		
		Returns
		-------
		bool
			True if `prefix` is valid

		"""
		return prefix in cls.__prefixes.keys()

	@classmethod
	def validPrefixes(cls):
		"""Return a tuple of the valid prefixes

		Returns
		-------
		:obj:`tuple` of :obj:`str`

		"""
		return tuple(cls.__prefixes.keys())

	__autoOutputPrefix = False
	@classmethod
	def setAutoOutputPrefix(cls, bool_):
		"""Set to display values with prefixes or not.

		Parameters
		----------
		bool_ : bool
			If `True`, automatically display uncercainties with prefixes.

		"""
		if bool_ in [True, False]: cls.__autoOutputPrefix = bool_
		else: raise ValueError("bool_ must be a bool, not type '{}'".format(type(bool_)))
	
	@classmethod
	def _getOtherValueUnc(cls, other):
		"""Return the appropriate `(value, unc)` tuple of `other`.
		
		Parameters
		----------
		other : any

		Returns
		-------
		:obj:`tuple`
			2-tuple of `(value, unc)` if `other` can be intepreted as a
			measurement.
		
		Raises
		------
		TypeError
			Indicates that `other` cannot be interpreted as a measurement.

		Notes
		-----
		If the constructor is cleaned up/decently efficient then it may be
		better to attempt to typecast to `cls` then extract `(val,unc)`.

		It is undecided whether the stricter type(other) == cls is desired over
		isinstance.

		The ducktyping x==float(x), from crude testing, appears faster than the
		old isinstance(x, (int,float)).
		
		"""
		if isinstance(other, cls): return (other.val, other.unc)
		
		# Ducktyping 'is number'
		try: floatOther = float(other)
		except TypeError: 
			raise NotImplementedError

		if other == floatOther: return (other, 0)
		raise NotImplementedError
			

	## PROPERTIES ##
	@property
	def val(self):
		""":obj:`float`: Value of the measurement."""
		return self._val

	@val.setter
	def val(self, value):
		if not isinstance(value, (int, float)):
			raise TypeError("value must be a float or int, not type '{}'".format(type(value)))
		self._val = value

	@val.deleter
	def val(self):
		del self._val

	@property
	def unc(self):
		""":obj:`float`: Uncertainty of the measurement."""
		return self._unc

	@unc.setter
	def unc(self, value):
		if not isinstance(value, (int, float)):
			raise TypeError("uncertainty must be a float or int, not type '{}'".format(type(value)))
		if value < 0:
			raise ValueError("uncertainty must be positive, not '{}'".format(value))
		self._unc = value

	@unc.deleter
	def unc(self):
		del self._unc

	
	## CONSTRUCTOR ##
	def __init__(self, val, unc = 0, scale = 1):
		"""Initialise an uncertainty object: `val+-unc * scale`

		Note: scale can be a number or any metric unit prefix ('p', 'n', 'u',
		'm', '', 'k', 'M', 'G', 'T')
		Note: this assumes <unc> is an ABSOLUTE uncertainty

		Parameters
		----------
		val : float
			The measured valued.
		unc : :obj:`float`, optional
			The measurement's associated uncertainty. Default `0`.
		scale : :obj:`float`, :obj:`str`, optional
			The scale of both `value` and `uncertainty`. Can either be a number
			of a valid prefix. Default `1`.

		"""
		if isinstance(val, type(self)) and unc==0 and scale==1: #only allowed if unc and scale are default values
			self.val = val.val
			self.unc = val.unc
		elif isinstance(scale, (int, float)):
			self.val = val * scale
			self.unc = unc * scale
		elif scale in self.__prefixes:
			scale = self.prefixToScale(scale)
			self.val = val * scale
			self.unc = unc * scale
		else:
			raise ValueError("scale must be a prefix or a number, not type '{}'".format(type(scale)))


	## RICH COMPARISONS ##
	def __eq__(self, b):
		"""Equality check. 
		
		Assumes that if `b` is an Uncertainty class, i.e. it has numerical
		`b.unc`	and `b.val` attributes.

		"""
		try:
			b_unc = b.unc
			b_val = b.val
		except AttributeError:
			b_unc = 0
			b_val = b
		return self.val == b_val and self.unc == b_unc

	def __ne__(self, b): return not (self == b)


	## OPERATIONS ##
	def __abs__(self): return type(self)(abs(self.val), self.unc)

	def __pos__(self): return self
	
	def __neg__(self): return type(self)(-self.val, self.unc)
	
	def __add__(self, b): raise NotImplementedError

	def __radd__(self, b): return self + b

	def __sub__(self, b): raise NotImplementedError
	
	def __rsub__(self, b): return -self + b

	def __mul__(self, b): raise NotImplementedError
	
	def __rmul__(self, b): return self * b

	def __truediv__(self, b): raise NotImplementedError

	def __rtruediv__(self, b): raise NotImplementedError

	def __pow__(self, b): raise NotImplementedError

	def __rpow__(self, b): raise NotImplementedError

	def __iadd__(self, b): return self + b

	def __isub__(self, b): return self - b

	def __imul__(self, b): return self * b

	def __itruediv__(self, b): return self / b

	def __ipow__(self, b): return self ** b


	## METHODS ##
	def findBestPrefix(self):
		"""Find the best prefix to represent this measurement's value. 

		That being the one gives the smallest number of significant figures
		above the decimal point (so long as there is at least one).

		Returns
		-------
		str
			The appropriate prefix

		"""
		prefixes = list(self.__prefixes.items())
		prefixes.sort(key=lambda x: x[1])

		differences = [] # == number of digits above the decimal point - 1 if this prefix is applied
		for (i, prefixScale) in enumerate(prefixes):
			numDigits = math.floor( math.log10(abs( self.val/prefixScale[1] )) )
			differences.append( (prefixScale[0], numDigits) )
		
		if differences[0][1] < -2:
			bestPrefix = ""
		elif differences[-1][1] > 2:
			bestPrefix = ""
		else:
			bestPrefix = min(differences, key=lambda x: abs(x[1]))[0]
			
		return bestPrefix

	def percent(self):
		"""Return the percentage uncertainty of itself (uncertainty/value)
		
		Returns
		-------
		float
			`self.unc/self.val`
		
		"""
		return self.unc / self.val

	def maxVal(self):
		"""Return the maximum value a measurement could take within the bounds
		of its uncertainty.

		Useful for e.g. basing an uncertainty off of a range of values, which
		has bounds which are themselves measurements:
			Aa (upper bound)
			Bb (lower bound)
		=> e.g. CoherentMeasurement(val, (Aa.maxVal() - Bb.minVal())/2)
		
		Returns
		-------
		int, float

		"""
		return self.val + self.unc

	def minVal(self):
		"""Return the minumum value a measurement could take within the bounds
		of its uncertainty.
		
		Returns
		-------
		int, float
		"""
		return self.val - self.unc


	## TYPECASTING AND DISPLAYING ##
	def __hash__(self): 
		if self.unc == 0:
			return hash(self.val)
		return hash((self.val, self.unc))

	def __bool__(self): return self.val != 0 or self.unc != 0

	def __float__(self):
		#raise NotImplementedError("This shouldn't be a thing as this is a value WITH AN UNCERTAINTY, but it might be useful... (say, for numpy arrays)")
		#Commented - it's useful for pd dataframes when doing mean, std etc.
		return self.val

	def __str__(self):
		if self.__autoOutputPrefix:
			return self.reprWithPrefix()
		return str(self.val) + " +- " + str(self.unc)

	def reprWithPrefix(self, prefix=None):
		"""Return a representation of the uncertainty object with the
		appropriate prefix to minimise unnecessary displayed 0s.

		TODO: 
		- There appears to be some unnecessary steps in the main 'else'

		Parameters
		----------
		prefix : :obj:`str`, optional
			If specified, forcces the representation to be with that prefix
		
		Returns
		-------
		str

		"""
		returnString = ""

		if prefix != None:
			if self.isValidPrefix(prefix):
				scale = self.__prefixes[prefix]
				returnString = str(self.val / scale) + " +- " + str(self.unc / scale) + " prefix:" + prefix
			else:
				raise ValueError("'{}' isn't a valid prefix".format(prefix))
		
		else:
			bestPrefix = self.findBestPrefix()
			bestScale = self.prefixToScale(bestPrefix)
			if bestPrefix == '':
				returnString = str(self.val) + " +- " + str(self.unc)
			else:
				returnString =  str(self.val / bestScale) + " +- " + str(self.unc / bestScale) + " | prefix:" + bestPrefix
		
		if returnString == '':
			returnString = str(self.val) + " +- " + str(self.unc)
		return returnString

	def __repr__(self): return str(self)


class CoherentUncertainty(_Uncertainty_Prototype):
	"""Uncertainty class for values with ABSOLUTE uncertainties -> value +-
	uncertainty
	
	(Coherent as in everything has the same sign)

	Operations follow the following: let f(x,y) be a function, then the 
	uncertainty of f(Aa,Bb) is 
		`fx(A,B)*a + fy(A,B)*b`

	This allows for all basic arithmetic operations on uncertainty objects
	(and between uncertainty objects and numbers, which are interpreted as
	uncertainty objects with 0 uncertainty). The operations between two
	uncertainty objects x=A+-a and y=B+-b are:
		`x+y = (A+B) +- (a+b)`

		`x-y = (A-B) +- (a+b)`

		`x*y = (A*B) +- (A*B * (a/A + b/B))`

		`x/y = (A/B) +- (A/B * (a/A + b/B))`

		`x**y= (A**B) +- (A**B * (a*B/A + b*math.log(A))`

		`unc.log(x,y) = math.log(A,B) +- (math.log(A,B) * (a/(A*math.log(A)) + b/(B*math.log(B))))`
	
	Attributes
	----------
	__suppress_IncoherenceMessages : bool
		Suppress warnings about possible incorrect calculations. (This should
		be a property)
	
	"""

	## CLASSMETHODS ##
	#this would be better as a class property than separate getter/setters
	__suppress_IncoherenceMessages = False
	@classmethod
	def suppress_IncoherenceMessages(cls, bool_ = None):
		"""suppress the Incoherent Uncertainty warnings if True
		
		using `bool_ = None` retrieves `__suppress_IncoherenceMessages`,
		otherwise, attempts to set `__suppress_IncoherenceMessages`.

		Parameters
		----------
		bool_ : bool

		"""
		if bool_ == None:
			return cls.__suppress_IncoherenceMessages
		if bool_ in [True, False]:
			cls.__suppress_IncoherenceMessages = bool_
		else:
			raise TypeError("bool_ must be a bool, not type '{}'".format(type(bool_)))


	## CONSTRUCTOR ##
	def __init__(self, val, unc = 0, scale = 1):
		"""Initialise a CoherentUncertainty object: `val+-unc * scale`
		
		Note: scale can be a number or any metric unit prefix ('p', 'n', 'u', 
		'm', '', 'k', 'M', 'G', 'T'), or a real number

		Parameters
		----------
		val : float
			The measured valued.
		unc : :obj:`float`, optional
			The measurement's associated uncertainty. Default `0`.
		scale : :obj:`float`, :obj:`str`, optional
			The scale of both `value` and `uncertainty`. Can either be a number
			of a valid prefix. Default `1`.

		"""
		super().__init__(val, unc, scale)
	
	## OPERATIONS ##
	def __add__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		return type(self)(A+B, a+b)
	
	def __sub__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		return type(self)(A-B, a+b)
	
	def __mul__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		if A*B < 0 and not self.suppress_IncoherenceMessages():
			print("WARNING: {0}*{1} results in an incoherent uncertainty, but is not corrected in calculations".format(A,B))
		return type(self)(A*B, B*a + A*b)
	
	def __truediv__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		if A*B < 0 and not self.suppress_IncoherenceMessages():
			print("WARNING: {0}/{1} results in an incoherent uncertainty, but is not corrected in calculations".format(A,B))
		return type(self)(A/B, a/B + A*b/(B**2))
	
	def __rtruediv__(self, other):
		B, b = self.val, self.unc
		try: A, a = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented

		if A*B < 0 and not self.suppress_IncoherenceMessages():
			print("WARNING: {0}/{1} results in an incoherent uncertainty, but is not corrected in calculations".format(A,B))
		return type(self)(A/B, a/B + A*b/(B**2) )

	def __pow__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented

		if A == 0:
			#I suspect --> result is 0+-0... however, the uncertainty on A means that this could actually be a very tiny value below/above 0 (or massive, if |B|<<1)
			raise ValueError("0**anything where 0 is an uncertainty cannot be calculated. +++This requires GeneralUncertainty objects")
		if A < 0:
			#if type(B) != int: raise ValueError("{0}**{1} is complex, so an uncertainty calculation cannot be done".format(A,B))
			raise ValueError("{} is negative, so an uncertainty calculation involving it to any power cannot currently be done".format(A)) #log(-ve) --> complex
		
		X = A**B
		if 0 < A <= 1:
			#raise RunTimeWarning("The base of a power is less than one, this will likely cause an incoherent uncertainty, but this hasn't been accounted for. It is advised to use IncoherentUncertainty objects instead")
			if b != 0 and not self.suppress_IncoherenceMessages(): 
				print("WARNING: The base of a power is less than one, this will likely cause an incoherent uncertainty, but this hasn't been accounted for. It is advised to use IncoherentUncertainty objects instead")
			return type(self)(X, X*(B*a/A + math.log1p(A-1)*b) )
		else:
			return type(self)(X, X*(B*a/A + math.log(A)*b) )

	def __rpow__(self, other):
		B, b = self.val, self.unc
		try: A, a = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented

		if A == 0:
			#I suspect --> result is 0+-0... however, the uncertainty on A means that this could actually be a very tiny value below/above 0 (or massive, if |B|<<1)
			raise ValueError("0**anything where 0 is an uncertainty cannot be calculated. +++This requires GeneralUncertainty objects")
		if A < 0:
			if type(b.val) != int: raise ValueError("{0}**{1} is complex, so an uncertainty calculation cannot be done".format(A,B))
			else: raise ValueError(str(A) + "is negative, so an uncertainty calculation involving it to any power cannot currently be done") #log(-ve) --> complex
		
		X = A**B
		if 0 < A <= 1:
			#raise RuntimeWarning("The base of a power is less than one, this will likely cause an incoherent uncertainty, but this hasn't been accounted for. It is advised to use IncoherentUncertainty objects instead")
			if b != 0 and not self.suppress_IncoherenceMessages(): 
				print("WARNING: The base of a power is less than one, this will likely cause an incoherent uncertainty, but this hasn't been accounted for. It is advised to use IncoherentUncertainty objects instead")
			return type(self)(X, X*(B*a/A + math.log1p(A-1)*b) )
		else:
			return type(self)(X, X*(B*a/A + math.log(A)*b) )


class CoherentUncertaintyForced(_Uncertainty_Prototype):
	"""
	Operations follow the following: let f(x,y) be a function, then the 
	uncertainty of f(Aa,Bb) is 
		`abs(fx(A,B)*a) + abs(fy(A,B)*b)`

	"""

	def __init__(self):
		return NotImplementedError


class IncoherentUncertainty(_Uncertainty_Prototype):
	"""Uncertainty object assuming all uncertainties are incoherent.

	=> this calculates standard error instead of maximum uncertainty

	Operations follow the following: let f(x,y) be a function, then the 
	uncertainty (actually standard error) of f(Aa,Bb) is 
		`sqrt( (fx(A,B)*a)**2 + (fy(A,B)*b)**2) )`

	Supports operations: ** * / + -

	(Also note that log() hasn't been adjusted to include this function)

	"""

	#def __init__(self, val, unc, scale):
	#	"""Note that this does not need a separate __init__ function"""
	#	raise NotImplementedError()
	
	## OPERATIONS ##
	def __add__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		return type(self)(A+B, math.sqrt(a**2 + b**2))
	
	def __sub__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		return type(self)(A-B, math.sqrt(a**2 + b**2))
	
	def __mul__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		return type(self)(A*B, math.sqrt((B*a)**2 + (A*b)**2))
	
	def __truediv__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		return type(self)(A/B, math.sqrt((a/B)**2 + (A*b/(B**2))**2))
	
	def __rtruediv__(self, other):
		B, b = self.val, self.unc
		try: A, a = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented
		return type(self)(A/B, math.sqrt((a/B)**2 + (A*b/(B**2))**2))

	def __pow__(self, other):
		A, a = self.val, self.unc
		try: B, b = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented

		if A == 0:
			#I suspect --> result is 0+-0... however, the uncertainty on A means that this could actually be a very tiny value below/above 0 (or massive, if |B|<<1)
			raise ValueError("0**anything where 0 is an uncertainty cannot be calculated. +++This requires GeneralUncertainty objects")
		if A < 0:
			if type(b.val) != int: raise ValueError("{0}**{1} is complex, so an uncertainty calculation cannot be done".format(A,B))
			else: raise ValueError(str(A) + "is negative, so an uncertainty calculation involving it to any power cannot currently be done") #log(-ve) --> complex
		
		X = A**B
		if 0 < A <= 1:
			return type(self)(X, abs(X)*math.sqrt((B*a/A)**2 + (math.log1p(A-1)*b)**2))
		else:
			return type(self)(X, abs(X)*math.sqrt((B*a/A)**2 + (math.log(A)*b)**2))

	def __rpow__(self, other):
		B, b = self.val, self.unc
		try: A, a = self._getOtherValueUnc(other)
		except TypeError: return NotImplemented

		if A == 0:
			#I suspect --> result is 0+-0... however, the uncertainty on A means that this could actually be a very tiny value below/above 0 (or massive, if |B|<<1)
			raise ValueError("{0}**{1} is complex, so an uncertainty calculation cannot be done".format(A,B))
		if A < 0:
			if type(b.val) != int: raise ValueError(str(A) + "**" + str(B) + "is complex, so an uncertainty calculation cannot be done")
			else: raise ValueError(str(A) + "is negative, so an uncertainty calculation involving it to any power cannot currently be done") #log(-ve) --> complex
		
		X = A**B
		if 0 < A <= 1:
			return type(self)(X, abs(X)*math.sqrt((B*a/A)**2 + (math.log1p(A-1)*b)**2))
		else:
			return type(self)(X, abs(X)*math.sqrt((B*a/A)**2 + (math.log(A)*b)**2))


class GeneralUncertainty(_Uncertainty_Prototype):
	"""Generalised approach to uncertainties. 
	
	See "Factorio" exercise book for the idea on how this'll work

	Assorted notes:
	- Use a try-except to avoid infinities/errors
	- Double check that the uncertainty gets swapped for subtraction (x-y 
	  should be the same as x+(-y))'
	- It's worth noting that thinking about -1*x = -x is the basis for why
	  the uncertainty gets flipped - as it's reflecting across the origin
	
	TODO:
	- Get the prototype to play nice (or just make this class independent)
	- make repr() sensible, at the moment it's "val +- (lower, upper)" which
	  is visually confusing
	- multiply/divide could be done explicitly

	WARNINGS:
	- estimateUncertainty is not fullproof/trustworthy yet
	"""

	#CLASSMETHODS and STATICMETHODS
	@classmethod
	def _getOtherValUnc(cls, other):
		"""Return a tuple (val, unc) for <value>
		
		Notes
		-----
		See IncoherentUncertainty._getOther_ValueUnc for a little discussion on
		this function's implementation. This should be put into the 
		`_Uncertainty_Prototype`... hmm, perhaps not due to unc being a tuple
		not a number it would also be better to leave the interpretation of
		floats etc. up to __init__ to be standardised (& in one place)
		
		"""
		raise NotImplementedError("Legacy function")
		if isinstance(other, cls):
			B = other.val
			b = other.unc
		elif isinstance(other, (float, int)):
			B = other
			b = (0, 0)
		else:
			return NotImplemented
		return (B,b)

	@classmethod
	def minimise(cls, f, start, domain, precision=5, test_domain_corners=True,
				 useDynamicStepSize=True, *args, **kwargs):
		"""equivalently maximise -f"""
		return -cls.maximise(
			lambda *x: -f(*x),
			start,
			domain,
			precision,
			test_domain_corners,
			useDynamicStepSize,
			*args,
			**kwargs
		)

	@classmethod
	def maximise(cls, f, start, domain, precision=5, test_domain_corners=True,
				 useDynamicStepSize=True, *args, **kwargs):
		"""Return the maximum value of function `f(*params)` over `domain` to
		`precision`

		It might be more useful to return the values that give the max value!
		(NO, as multiple values might give the same maximum! (eg. if an
		absolute value function of a plane -> a line of infinite values give
		the same max)).
		
		Parameters
		----------
		start : :obj:`tuple` of :obj:`float`
			Tuple of starting values.
		domain : :obj:`tuple` of :obj:`tuple` of :obj:`float`
			Tuple of tuples of domain to check.
		precision : int
			Number of decimal places below the most significant figure of each
			value is to be checked.
		test_domain_corners : bool
			if True, also tries starting at all 'corners' of the rectangular
			domain. (adds 2**len(domain) starting points)
		useDynamicStepSize : bool
			if True, this will start at a lower precision for each start value,
			decreasing how much each parameter can change until the desired
			precision is reached.

		Notes
		-----
		Note that domain is a tuple of pairs, where each pair is the valid domain of the appropriate parameter

		Current issues: 
		- precision is tripping up the domain due to floating point errors. 
		  It would be better to give a direct solution rather than "check the 
		  boundaries of the domain explicitly"
		  (I've added domain checking to reduce possibility of only finding local extrema
		  but the usual search should be able to reach the boundaries!)
		- Possibility of errors in function execution should be dealt with (use
		  try-except to avoid where the function is undefined)
		
		"""

		##### WARNING: This is not thoroughly tested. sin(x)*e^(-y) is an obvious case where the algorithm fails 


		#Type checking
		#For now I'll assume everything is correct type

		#Preparing
		if test_domain_corners:
			starting_points = asd.iterOverIterables([start], asd.permuteOptions(domain))
		else: starting_points = [start]

		maxPrecs = []
		for p in start:
			if p == 0:
				maxPrecs.append(10**(-precision))
			else:
				maxPrecs.append(10 ** (math.floor( math.log10(abs(p)) ) - precision))
		if useDynamicStepSize:
			precs = []
			for p in start:
				if p == 0:
					precs.append(1)
				else:
					precs.append(10 ** (math.floor( math.log10(abs(p)) )))
		else: precs = maxPrecs

		#Search
		maxPoints = [] #Keeps track of the parameter values, and function values. (Might be useful if I ever want the points)
		for start in starting_points:
			maxed = False
			currentPoint = start
			currentVal = f(*currentPoint, *args, **kwargs)
			while not maxed:
				#New points to check
				oldPoint, oldVal = currentPoint, currentVal
				perms = []
				for p, d, prec in zip(currentPoint, domain, precs): #possible paramter values that are within domain
					perm = [p]
					if d[0] <= p + prec <= d[1]:
						perm.append(p + prec)
					if d[0] <= p - prec <= d[1]:
						perm.append(p - prec)
					perms.append(perm)

				#Function value check
				pointsGiveMax = True
				for perm in asd.permuteOptions(perms):
					newVal = f(*perm, *args, **kwargs)
					if newVal > currentVal:
						currentVal = newVal
						currentPoint = perm
						pointsGiveMax = False
				if pointsGiveMax:
					maxed = True
				
				#Adjust step sizes
				if useDynamicStepSize:
					for i, (oldParam, currentParam, prec, maxPrec) in enumerate(zip(oldPoint, currentPoint, precs, maxPrecs)):
						if oldParam == currentParam and prec > maxPrec:
							precs[i] = prec / 10 #I am concerned about losing precision in this value though...
							maxed = False
			maxPoints.append((currentPoint, currentVal))
		maxEstimate = max(maxPoints, key=lambda x: x[1])
		return maxEstimate[1]

	@classmethod
	def minimise_fullDomainCheck(cls, f, domain, precision=5, *args, **kwargs):
		"""equivalently maximise -f"""
		return -cls.maximise_fullDomainCheck(lambda *x: -f(*x), domain, precision, *args, **kwargs)

	@classmethod
	def maximise_fullDomainCheck(cls, f, domain, precision=5, *args, **kwargs):
		"""Maximises the function by manually checking the ENTIRE parameter space
		
		Assumes <domain> is an iterable of closed intervals

		This is necessary for functions like f(x) = sin(x) * e^(-x)
		"""
		precs = []
		for (p_lower,p_upper) in domain:
			p = (p_lower + p_upper) / 2
			if p == 0:
				precs.append(10**(-precision))
			else:
				precs.append(10 ** (math.floor( math.log10(abs(p)) ) - precision))
		precs = tuple(precs)
		start = tuple([d[0] for d in domain])
		stop = tuple([d[1]+prec for (d,prec) in zip(domain, precs)])
		maxVal = f(*start, *args, **kwargs)
		for point in asd.multirange(start, stop, precs, allowFloats=True):
			val = f(*point, *args, **kwargs)
			if val > maxVal:
				maxVal = val
		return maxVal

	@classmethod
	def estimateUncertainty(cls, f, uncertaintyArgs, precision=5, 
							test_domain_corners=False, fullDomainCheck=False,
							useDynamicStepSize=True, *args, **kwargs):
		"""Return the uncertainty object that results from passing the
		`GeneralUncertainty` instances `uncertaintyArgs` through function `f`.
		
		Function will get called by:
			`f(*vals, *args, **kwargs)`
		where:
			`vals = [measurement.val for measurement in uncertaintyArgs]`

		For now, this assumes that uncertaintyArgs is a tuple of GeneralUncertainty objects

		Parameters
		----------
		f : function
			Function to estimate.
		uncertaintyArgs : :obj:`list` of :obj:`GeneralUncertainty`
			Iterable of the uncertainty objects that get passed to `f`.
		precision : int
			Number of decimal places below the most significant figure of each
			value is to be checked.
		test_domain : bool
			If `True`, also tries starting at all 'corners' of the rectangular
			domain. (Adds `2**len(domain)` starting points)
		fullDomainCheck : bool
			If `True`, steps through the entire parameter space. If `False`,
			will use `vals` as a starting point in a 'simplex search' (I think
			that's what I'm doing??)
		useDynamicStepSize : bool
			If `True`, this will start at a lower precision for each start
			value, decreasing how much each parameter cane change until the
			desired precision is reached. (Only used if 
			`fullDomainCheck==False`)

		"""
		vals = []
		uncertaintyArgs_limits = []
		for measurement in uncertaintyArgs:
			val, unc = measurement.val, measurement.unc
			vals.append(val)
			uncertaintyArgs_limits.append((val-unc[0], val+unc[1]))

		Z = f(*vals, *args, **kwargs)
		if fullDomainCheck:
			z_lower = Z - cls.minimise_fullDomainCheck(f, uncertaintyArgs_limits, precision, *args, **kwargs)
			z_upper = cls.maximise_fullDomainCheck(f, uncertaintyArgs_limits, precision, *args, **kwargs) - Z
		else:
			z_lower = Z - cls.minimise(f, vals, uncertaintyArgs_limits, precision, test_domain_corners, useDynamicStepSize,  *args, **kwargs)
			z_upper = cls.maximise(f, vals, uncertaintyArgs_limits, precision, test_domain_corners, useDynamicStepSize, *args, **kwargs) - Z
		return cls(Z, (z_lower, z_upper))


	## PROPERTIES ##
	@property
	def unc(self):
		"""Uncertainty (lower, upper) of the measurement"""
		return self._unc

	@unc.setter
	def unc(self, value):
		if not isinstance(value, tuple):
			raise TypeError("uncertainty must be a tuple of (lowerunc, upperunc)")
		if len(value) != 2:
			raise ValueError("uncertainty must be a tuple of (lowerunc, upperunc)")
		if not (isinstance(value[0], (int, float)) and isinstance(value[1], (int, float))):
			raise TypeError("uncertainty must be a float or int, not type '" + str(type(value[0])) + "' and '" + str(type(value[1]))+ "'")
		if value[0] < 0 or value[1] < 0:
			raise ValueError("uncertainties must be positive, not '" + str(value) + "'")
		self._unc = value

	@unc.deleter
	def unc(self):
		del self._unc
	

	## CONSTRUCTOR ##
	def __init__(self, val, unc=(0,0), scale=1):
		"""Uncertainty object with numerical estimation of maximum uncertainty.
		
		Has methods for supporting arbitrary functions

		If <val> is of class `GeneralUncertainty`, then all other parameters
		will be ignored	and this constructor will return an idental copy of
		`val`.

		Parameters
		----------
		val : float
			Value of the measurement
		unc : :obj:`tuple` of :obj:`float`
			2-tuple of (lower, upper) uncertainty of the measurement

		"""
		if isinstance(val, type(self)):
			self.val = val.val
			self.unc = val.unc
		else:
			if not isinstance(unc, tuple) or len(unc) != 2:
				raise ValueError("<unc> must be a tuple of length 2")
			#if scale in self.__prefixes:   Not used for now, until the prototype can handle the new uncertainty
			#	scale = self.prefixToScale(scale)
			if isinstance(scale, (int, float)):
				self.val = val * scale
				self.unc = (unc[0] * scale, unc[1] * scale)
			else:
				raise ValueError("<scale> must be a valid prefix, or a number, not " + str(scale))


	## OPERATIONS ##
	def __neg__(self):
		# To see why the uncertainty gets flipped, consider reflecting a point
		# on the x-axis that has an uncertainty. The furthermost uncertainty
		# should remain the furmost uncertainty after reflection.
		return type(self)(-self.val, (self.unc[1], self.unc[0]))

	def __add__(self, other):
		A, a = self.val, self.unc
		try:
			other = type(self)(other)
		except TypeError:
			return NotImplemented
		B, b = other.val, other.unc
		return type(self)(A+B, (a[0]+b[0], a[1]+b[1]))

	def __sub__(self, other):
		#This one can be written explicitly
		A, a = self.val, self.unc
		try:
			other = type(self)(other)
		except TypeError:
			return NotImplemented
		B, b = other.val, other.unc
		return type(self)(A-B, (a[0]+b[0], a[1]+b[1]))

	def __mul__(self, other):
		#This one can't be done explicitly, but can be done simply
		try:
			other = type(self)(other)
		except TypeError:
			return NotImplemented
		Z = self.val*other.val
		self_extrema = [self.val-self.unc[0], self.val+self.unc[1]]
		other_extrema = [other.val-other.unc[0], other.val+other.unc[1]]
		result_extrema = []
		for (Aa,Bb) in asd.permuteOptions([self_extrema, other_extrema]):
			result_extrema.append(Aa*Bb)
		z_min = Z - min(result_extrema)
		z_max = max(result_extrema) - Z
		return type(self)(Z, (z_min, z_max))

	def __truediv__(self, other):
		try:
			other = type(self)(other)
		except TypeError:
			return NotImplemented
		return self.estimateUncertainty(lambda x,y: x/y, (self,other))

	def __rtruediv__(self, other):
		try:
			other = type(self)(other)
		except TypeError:
			return NotImplemented
		return self.estimateUncertainty(lambda x,y: y/x, (self,other))

	def __pow__(self, other):
		try:
			other = type(self)(other)
		except TypeError:
			return NotImplemented
		return self.estimateUncertainty(lambda x,y: x**y, (self,other))

	def __rpow__(self, other):
		try:
			other = type(self)(other)
		except TypeError:
			return NotImplemented
		return self.estimateUncertainty(lambda x,y: y**x, (self,other))


	## TYPECASTING AND DISPLAYING ##
	def __str__(self):
		return "<-{0} | {1} | +{2}>".format(self.unc[0], self.val, self.unc[1])
		

class FileHandler:
	"""Handle files of uncertainty data

	This version of FileHandler uses csv and stores data in pandas Dataframes,
	and returns the Dataframe.

	<inFilePath> must be the complete path (e.g. starting with C:/Users/ ...)

	.csv formatted as:
		variable1,       scale1, varaible2,       scale2, variable3,       scale3, ...
		   value1, uncertainty1,    value1, uncertainty1,    value1, uncertainty1, ... 
		   value2, uncertainty2,    value2, uncertainty2,    value2, uncertainty2, ... 

	IMPROVEMENTS:
	- turn this into a wrapper for a DataFrame object - inherits all functions etc.
	  from pd.DataFrame, but just acts on the .df attribute
	  https://stackoverflow.com/questions/1443129/completely-wrap-an-object-in-python
	"""

	## CONSTRUCTOR ##
	def __init__(self, inFilePath, columnOffset = 0, rowOffset = 0, uncertaintyType = "Incoherent"):
		raise NotImplementedError("This behaviour is not ready, and will hopefully be the basis of 0.3.0")
		self.df, self._extra_info = self.load(inFilePath, columnOffset, rowOffset, uncertaintyType)


	@classmethod
	def load(cls, inFilePath, columnOffset = 0, rowOffset = 0, uncertaintyType = "Incoherent"):
		"""Return the data. 
		
		This should also return an 'extra data' array that just contains all
		the unused stuff in the .csv file - that way you can write it back it.
		(just the headers - I had a better idea for extra cols)

		Parameters
		----------
		inFilePath : str
			FULL directory path to the csv file
		columnOffset : int
			Zero-based index of the column to start reading from (NOTE: this
			must include the variable headers)
		rowOffset : int
			Zero-based index of the row to start reading from
		uncertaintyType : str
			`"Incoherent"` or `"Coherent"`

		Returns
		-------
		pandas.DataFrame
			Compiled data (using the specified uncertainty class)
		:obj:`dict` of :obj:`list` and :obj:`dict`
			Extra_info dict (which can be edited to change what prefix measurements get saved as). Used to export the
			data back to a .csv.
			
		"""
		# TYPECHECKING
		if not isinstance(inFilePath, str):
			raise TypeError("inFilePath must be a string, not a, '{}'".format(type(inFilePath)))
		if inFilePath[-4:] != ".csv":
			raise ValueError("inFile must be a .csv")
		if not os.path.exists(inFilePath):
			print("The specified file '{}' does not exist. This may be caused by using '\' instead of '/'".format(inFilePath))
		if not isinstance(columnOffset, int):
			raise TypeError("<columnStart> must be of type '{0}' not type '{1}'".format(int, type(columnOffset)))
		if not isinstance(rowOffset, int):
			raise TypeError("<columnStart> must be of type '{0}' not type '{1}'".format(int, type(rowOffset)))
		if uncertaintyType not in ["Coherent", "Incoherent"]:
			raise ValueError("uncertaintyType must be 'Coherent' or 'Incoherent'")

		# DATA
		with open(inFilePath, "r") as infile:
			reader = csv.reader(infile)
			header_lines = []
			for i in range(rowOffset): 
				header_lines.append(next(reader))
			lineNumber = rowOffset + 1

			# VARIABLE VALIDATION
			variables = cls._prepareVariableLine(next(reader)[columnOffset:], lineNumber)
			lineNumber += 1
			
			# LOADING DATA
			data = []
			for row in reader:
				data.append(cls._prepareDataLine(row[columnOffset:], variables, lineNumber, uncertaintyType))
				lineNumber += 1
		df = pd.DataFrame(data, columns=variables[::2])
		extra_cols = pd.read_csv(inFilePath, 
								usecols=list(range(columnOffset)),
								skiprows=rowOffset)
		combined_df = extra_cols.merge(df, left_index=True, right_index=True)

		# EXTRAS
		extra_info = {'header_lines': header_lines, 'columnOffset':columnOffset}
		col_scales = {}
		for variable, scale in zip(variables[::2], variables[1::2]):
			col_scales[variable] = scale
		extra_info['col_scales'] = col_scales

		return combined_df, extra_info

	@staticmethod
	def _prepareVariableLine(variables, lineNumber):
		"""Prepare the variables line in the file. 

		TODO:
		- update this to 0.2.2 (doesn't need to prepare for a StringExpression anymore)

		Parameters
		----------
		variables : str
			Line for the variables, directly read from the file without
			adjustment.
		lineNumber : int
			Line in the file, for error messages.
		
		Returns
		-------
		list
			In the same order as the file: `["variable", scale, "variable",
			scale, ...]`

		Raises
		------
		ValueError
			If the variables have invalid characters.

		"""
		if len(variables) % 2 != 0:
			raise ValueError("The variables line in the file must have 'variable, scale' pairs (ie 2 columns per variable)")

		for i in range(0, len(variables), 2):
			var = variables[i]
			for char in "()^*/+-":
				if char in var:
					raise ValueError("Variable '{0}' contains an illegal character: '{1}' on line {2}".format(var, char, lineNumber))

			if variables[i] == "":
				raise ValueError("Cannot have a variable that is a blank string. Please check your headers and try again (there should be a value every 2 columns, starting with the 1st column)")
			if variables[i] in variables[:i] + variables[i+1:]:
				raise ValueError("Cannot have two variables in the data with the same name. '{}'".format(variables[i]))

			scale = variables[i+1]
			try:
				scale = float(scale)
				variables[i+1] = scale
			except ValueError:
				if not _Uncertainty_Prototype.isValidPrefix(scale):
					raise ValueError("scale '" + scale + "' must be a number or any of " + str(_Uncertainty_Prototype.validPrefixes()))

		return variables

	@staticmethod
	def _prepareDataLine(row, variables, lineNumber, uncertaintyType):
		"""Prepare a row, assuming <lineVariables> is in the same order as
		read in. 

		Parameters
		----------
		row : str
			Row to prepare.
		variables : :obj:`list` of :obj:`str`
			Variables in the line, including the scale (`""`, a number, or one
			of `Uncertainty.__prefixes.keys()`)
		lineNumber : int
			Line in the file, for error messages.

		Returns
		-------
		list

		Raises
		------
		ValueError

		"""
		if len(row) % 2 != 0:
			raise ValueError("line {} does not have an even number of columns, i.e. there might be an uncertainty missing".format(lineNumber))
		for elem in row:
			if not asd.isFloatable(elem, acceptInf=True):
				raise ValueError("'{0}' Cannot be interpreted as a float, please put a valid numerical value. This is on line {1} in the file".format(elem, lineNumber))
		if len(variables) != len(row): 
			raise ValueError("Something unexpected occured, and the variables list does not have the same length as the line. This is on line {} in the file".format(lineNumber))

		valuesList = []
		if uncertaintyType == "Coherent":
			for i in range(0, len(variables), 2):
				val = float(row[i])
				unc = float(row[i+1])
				scale = variables[i+1]
				valuesList.append(CoherentUncertainty(val, unc, scale))
		elif uncertaintyType == "Incoherent":
			for i in range(0, len(variables), 2):
				val = float(row[i])
				unc = float(row[i+1])
				scale = variables[i+1]
				valuesList.append(IncoherentUncertainty(val, unc, scale))
		return valuesList

	@staticmethod
	def save(outFilePath, data, extra_info = None):
		"""Save the data to outFilePath.

		TODO: 
		- more elegant solution is to just use the csv module for saving pandas
		  is cool, but it isn't meant for this sort of thing.

		Parameters
		----------
		outFilePath : str
		data : `pd.DataFrame`
		extra_info : dict
			`extra_info` returned by `FileHandler.load()`

		"""
		
		# TYPE CHECKING
		if extra_info == None: 
			extra_info = {}
		elif type(extra_info) != dict:
			raise TypeError("'extra_info' must be 'None' or type 'dict', not type '{}'".format(type(extra_info)))
		extra_info['columnOffset'] = extra_info['columnOffset'] if extra_info.get('columnOffset', False) else 0
		extra_info['header_lines'] = extra_info['header_lines'] if extra_info.get('header_lines', False) else []
		extra_info['col_scales'] = extra_info['col_scales'] if extra_info.get('col_scales', False) else {}

		# SAVING HEADERS
		with open(outFilePath, 'w') as outfile:
			writer = csv.writer(outfile)
			writer.writerows(extra_info['header_lines'])
			
		# SAVING DATA
		out_df = data.iloc[:, :extra_info['columnOffset']] #extra preceding cols
		for data_colName, measurements in data.iloc[:, extra_info['columnOffset']:].items():
			scale = extra_info['col_scales'].get(data_colName, 1)
			scale_as_num = _Uncertainty_Prototype.prefixToScale(scale)
			vals = measurements.apply(lambda x: x.val/scale_as_num)
			uncs = measurements.apply(lambda x: x.unc/scale_as_num)
			# the whole np.array().T is because pd.DataFrame is acting strangely when I do pd.DataFrame([vals,uncs])
			if scale == 1:
				extracted_cols = pd.DataFrame(np.array([vals, uncs]).T, columns=[data_colName, ""])
			else:
				extracted_cols = pd.DataFrame(np.array([vals, uncs]).T, columns=[data_colName, scale])
			out_df = out_df.merge(extracted_cols, left_index=True, right_index=True) #adds _x and _y to uncertainty column names
		
		out_df = out_df.rename(lambda x: x[:-2] if x[-2:] in ['_x', '_y'] else x, axis="columns") #remove _x, _y from column names
		out_df.to_csv(outFilePath, mode='a', index=False)
		return



################################## FUNCTIONS ##################################
def log(x, base = math.e):
	"""math.log() but also supports UncertaintyFull objects. 
	
	Will return an UncertaintyFull object if the uncertainty of the returned
	value is non-zero.

	be aware that this is only accurate for x around 1 (read Propagation of
	Uncertainty for why)

	I'm going to do this in a less efficient, but more readable manner
	(compared to Uncertainty classes definition).
	
	"""
	raise NotImplementedError("Not completed/up-to-date")

	if type(x) == IncoherentUncertainty or type(base) == IncoherentUncertainty:
		raise NotImplementedError("log() does not currently work for IncoherentUncertainty objects. Try using CoherentUncertainty")
	if type(x) == CoherentUncertainty:
		A = x.val
		a = x.unc
		if type(base) == CoherentUncertainty:
			B = base.val
			b = base.unc
		else:
			try: float(base)
			except ValueError: raise TypeError("base must be floatable")
			B = base
			b = 0

	elif type(base) == CoherentUncertainty:
		try: float(x)
		except ValueError: raise TypeError("x must be floatable")
		A = x
		a = 0
		B = base.val
		b = base.unc

	else:
		try: float(x)
		except ValueError: raise TypeError("x must be floatable")
		try: float(base)
		except ValueError: raise TypeError("base must be floatable")
		A = x
		a = 0
		B = base
		b = 0

	if a == 0 and b == 0:
		return math.log(A,B)

	if A <= 0: raise ValueError("log(A, B) cannot be calculated with uncertain values for A<=0")
	if A == 1: raise ValueError("log(A, B) cannot be calculated with uncertain values for A==1")
	if B <= 0: raise ValueError("log(A, B) cannot be calculated with uncertain values for B<=0")

	# if a=0 and A=1, then L'Hospital's rule gives unc = val*(1/A + b/(B*math.log(B)))

	if 0 <= A <= 1:
		if 0 <= B <= 1:
			#print("a")
			val = math.log1p(A-1) / math.log1p(B-1)
			unc = val*(a/(A*math.log1p(A-1)) + b/(B*math.log1p(B-1)))
		else:
			#print("b", A, a, B, b)
			val = math.log1p(A-1) / math.log(B)
			unc = val*(a/(A*math.log1p(A-1)) + b/(B*math.log(B)))
	else:
		if 0 <= B <= 1:
			#print("c")
			val = math.log(A) / math.log1p(B-1)
			unc = val*(a/(A*math.log(A)) + b/(B*math.log1p(B-1)))
		else:
			#print("d")
			val = math.log(A,B)
			unc = val*(a/(A*math.log(A)) + b/(B*math.log(B)))
	if unc == 0:
		return val
	else:
		return CoherentUncertainty(val, unc)