"""A set of functions for builtins

A previous iteration had these be classes, with the whole premise being to
extend builtins with extra methods. However, in the long run this would be
non-maintainable and has a lot of chances to clash with modules tring to use
this. The superior solution is what was implemented here: a series of classes
containing static (or class) methods that take builtins as arguments, and
return builtins.

"""



################################### MODULES ###################################
import operator as op
import random
from os import stat



################################## CLASSES #####################################
class _AmbiguousMethods:
	"""A set of ambiguous methods that List, Str etc. may use."""


class Iterable:
	"""A set of methods that iterables can use."""

	@staticmethod
	def join(a, operator=op.__add__, sep=None, *args, **kwargs):
		"""Equivalent to javascript's Array.join().
		
		Parameters
		----------
		a : iterable
		operator : function
			Binary operator to use when combining elements. 
		sep : any
			Separator between elements. 
		*args
			Optional arguments to `operator`
		**kwargs
			Keyword arguments to `operator`

		Returns
		------
		any
			The result of combining every element using operator
		None
			If the iterator has an equivalent 0 length

		Raises
		------
		ValueError
			If not all elements in `a` can be combined
		
		"""
		a = iter(a)
		try:
			result = next(a)
		except(StopIteration):
			return None
		
		if sep == None:
			for elem in a:
				result = operator(result, elem, *args, **kwargs)
		else:
			for elem in a:
				halfway = operator(result, sep, *args, **kwargs)
				result  = operator(halfway, elem, *args, **kwargs)

		return result


class Str:
	"""Extra methods for :obj:`str` builtins"""

	@staticmethod
	def findAll(p, s):
		"""Yield all the positions of the pattern p in the string s.

		Parameters
		----------
		p : str
			Pattern to search for.
		s : str
			String to search through.

		Returns
		-------
		list
			Returns [] if none are found. Intended to all easier for loop
			integration than the original post.

		Yields
		------
		int
			A position of the pattern `p` in `s`.
		
		Notes
		-----
		Could also be accomplished with regex

		.. https://stackoverflow.com/questions/4664850/how-to-find-all-occurrences-of-a-substring

		"""
		i = s.find(p)
		if i == -1: return []
		while i != -1:
			yield i
			i = s.find(p, i+1)


class List(Iterable):
	"""Extra methods for :obj:`list` builtins
	
	This class does not have a constructor, and is intended to only be used as
	a static class for organising functions.
	"""

	@staticmethod
	def pairJoin(a, b, operator=op.__add__, sep=None, *args, **kwargs):
		"""Join two identical-length lists element-wise.

		Returns a single object, which is the combination of each element as
		`operator(elemA, elemB, *args, **kwargs)`, with optionally `separator`
		in between. 
		
		Parameters
		----------
		a : list
			First list
		b : list
			Second list. Must have same length as `a`
		operator : function
			Binary operator to use when combining elements. 
		sep : any
			Separator between elements.
		*args
			Optional arguments to `operator`
		**kwargs
			Keyword arguments to `operator`
		
		Returns
		-------
		list
			A list of combined elements
		
		Notes
		-----
		- Support for per-element operators and separators is not planned to be
		  implemented.
		- Support for `*args` and `**kwargs` will be dropped. It will be
		  assumed that the user creates an appropriate lambda function before
		  setting it to be the `operator`.

		"""
		# CHECKS
		if type(a) != list or type(b) != list:
			# This could be relaxed, and reserved to a try-except statement (to work for iterables)
			raise TypeError('Can only take objects of type {} as arguments'.format(list))
		if len(a) != len(b):
			raise ValueError('a and b must be of the same length')
		# May need more checks for confirming operator works... (have to implemented using try-except). Which may be
		# easier to do in the (# COMBINING LISTS) section. (Using for loops rather than list comprehension).

		# COMBINING LISTS
		combinedList = []
		if sep == None:
			for elemA, elemB in zip(a,b):
				combinedList.append(operator(elemA, elemB, *args, **kwargs))
		else:
			for elemA, elemB in zip(a,b):
				halfway = operator(elemA, sep, *args, **kwargs)
				combinedList.append(operator(halfway, elemB, *args, **kwargs))

		return combinedList
	
	@classmethod
	def convertElementType(cls, a, class_, allowSubLists=False):
		"""Convert every element of a list to type `class_`. 
		
		Parameters
		----------
		a : list
			List to convert elements of.
		class_ : type
			Type to convert elements to.
		allowSubLists : bool
			If True, then will recursively convert elements of sub-lists.
		
		Returns
		-------
		list
			List of converted elements
		
		"""
		newList = []

		if allowSubLists:
			for elem in a:
				if type(elem) == list:
					newList.append(cls.convertElementType(elem, class_, allowSubLists))
				else:
					newList.append(class_(elem))

		else:
			for elem in a:
				newList.append(class_(elem))
		
		return

	@staticmethod
	def randomise(a):
		"""Puts the elements of a list in a random order
		
		Parameters
		----------
		a : list
		
		Returns
		-------
		list

		"""
		a = a[:] # Copy
		n = len(a)
		new = []
		for i in range(n):
			index = random.randint(0, n-i-1)
			new.append(a.pop(index))
		return new

	@staticmethod
	def distinctify(a):
		"""Remove duplicate entries in a list"""
		### Another possible feature: pass a function to this, so that this can
		### check for distinct player.name in the list!!
		# Alternatively: list(set(a)), but that doesn't guaruntee order preservation
		a = a[:] # Copy
		i = 0
		while i < len(a):
			j = i+1
			while j < len(a):
				if a[j] == a[i]: a.pop(j)
				else: j += 1
			i += 1
		return a
	
	@staticmethod
	def rotate(a, n):
		"""Rotates the list to the right.
		
		Parameters
		----------
		a : list
			List to rotate
		n : int
			Number of places to rotate to the right. Negative indicates going
			left.
		
		Returns
		-------
		list

		"""
		if type(n) != int:
			raise TypeError('n must be of type {} not {}'.format(int, type(n)))
		
		length = len(a)
		n %= length
		if n > 0:
			return a[n:] + a[:n]
		else:
			return a[length-n:length] + a[:length-n]
		return
	
	@staticmethod
	def find(a, val, key=None):
		"""Return the the lowest index of an occurence of `value` in `a`.

		Parameters
		----------
		a : list
			List to search through.
		val : any
			Value to search for.
		key : :obj:`function`, optional
			If not `None`, then each element is checked by `key(elem)==val`
			instead.
		
		Returns
		-------
		int
			Index of element. -1 if element is not in list.
		
		"""
		if key == None:
			key = lambda x : x

		for (i, elem) in enumerate(a):
			if key(elem) == val: 
				return i
		return -1

	@classmethod
	def rfind(cls, a, val, key=None):
		"""Return the the highest index of an occurence of `value` in `a`.

		Parameters
		----------
		a : list
			List to search through.
		val : any
			Value to search for.
		key : :obj:`function`, optional
			If not `None`, then each element is checked by `key(elem)==val`
			instead.
		
		Returns
		-------
		int
			Index of element. -1 if element is not in list.
		
		"""
		return len(a) - cls.find(a.reverse(), val, key)


class Dict(Iterable):
	"""Methods for :obj:`dict` builtins."""
	
	@staticmethod
	def keysOf(a, val, key=None):
		"""Return a list of keys whose corresponding value is `val`
		
		Parameters
		----------
		a : dict
			Dict to check
		val : any
			Value to check for
		key : :obj:`function`, optional
			If not `None`, check for `key(dictVal)==val` instead.
		
		Returns
		-------
		list

		"""
		if key == None:
			key = lambda x : x

		return [k for (k,v) in a.items() if key(v)==val]
		
		# old (More maintainable if key() throws errors)
		keyList = []
		for (k,v) in a.items():
			if key(v) == val:
				keyList.append(k)
		return keyList


class Function:
	"""Methods about manipulating functions."""

	@staticmethod
	def numArgs(f, maxToCheck=100):
		"""Returns the number of arguments a function takes."""
		for i in range(maxToCheck): 
			try:
				f()
			except(TypeError):
				continue
			return i
		return float("inf")









