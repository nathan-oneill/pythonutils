"""An assortment of both usable and not usable functions"""



################################### MODULES ###################################
from types import FunctionType
import functools
import time
import math
import os



################################## CLASSES ####################################
class enumerate2:
	"""Enumerate with start, stop, step functionality.
	
	Equivalent to doing:
		for (i, elem) in enumerate(iterable):
			if (start <= i < stop and (i-start)%step==0): 
				#
				# Normal code here
				#

	which actually turns out faster.

	"""

	def __init__(self, iterable, start=0, stop=None, step=1):
		"""Enumerate, equivalently, over `iterable[start:stop:step]`

		Note: slice notation is not used, so is not required to be defined

		Parameters
		----------
		iterable : iterable
		start : int
		stop : int
		step : int

		"""
		try: 
			(e for e in iterable)
		except: 
			raise TypeError("an object of type '" + str(type(iterable)) + "' is not iterable.")
		if type(start) != int:
			raise TypeError("<start> must be of type 'int' not type '" + str(type(start)) + "'.")
		if stop != None and type(stop) != int:
			raise TypeError("<stop> must be of type 'int' not type '" + str(type(stop)) + "'.")
		if type(step) != int:
			raise TypeError("<step> must be of type 'int' not type '" + str(type(step)) + "'.")
		if step <= 0:
			raise ValueError("<step> must be a positive integer, not '" + str(step) + "'")
		if stop == None:
			stop = float('inf')

		acceptNegatives = True
		try:
			length = len(iterable)
		except TypeError:
			acceptNegatives = False

		if not acceptNegatives:
			for num in [start, stop]:
				if num < 0:
					raise ValueError("object of type '" + str(type(iterable)) + "' has no len(), so negative indexes cannot be interpreted")
		if step < 0:
			raise ValueError("step can only positive, not " + str(step))

		self.iterable = iterable
		self.start = start
		self.stop = stop
		self.step = step
		return

	def __iter__(self):
		if self.start < 0: 
			start = self.start + len(self.iterable)
		else: 
			start = self.start
		if self.stop < 0: 
			stop = self.stop + len(self.iterable)
		else: 
			stop = self.stop
		step = self.step

		if stop == float('inf'):
			i = 0 #more efficient if start at -start rather than calculating i-start each time
			for elem in self.iterable:
				if start <= i and (i-start)%step == 0:
					yield (i, elem)
				i += 1
		else:
			i = 0
			for elem in self.iterable:
				if start <= i < stop and (i-start)%step == 0:
					yield (i, elem)
				if i >= stop:
					break
				i += 1
		return
	
	def __iter2__(self):
		"""A possibly more efficient approach. Unfortanetely, this isn't the
		place to raise StopIteration
		
		"""
		raise NotImplementedError()
		if self.start < 0: 
			start = self.start + len(self.iterable)
		else: 
			start = self.start
		if self.stop < 0: 
			stop = self.stop + len(self.iterable)
		else: 
			stop = self.stop
		step = self.step

		#Double check the output
		iterObj = iter(self.iterable)
		for i in range(start):
			next(iterObj)
		if stop == float('inf'):
			if step == 1:
				i = start
				while True:
					yield (i, next(iterObj))
					i += 1
			else:
				i = start
				while True:
					if (i - start)%step == 0:
						yield (i, next(iterObj))
					i += 1
		else:
			for i in range(start, stop, step):
				yield (i, next(iterObj))
		return
	
	def __iter_best_idea(self):
		rangeObj = range(self.start, self.stop, self.step) #this could be improved by making a list, then doing a binary search for i instead
		for (i, elem) in enumerate(self.iterable):
			if i in rangeObj:
				yield (i, elem)

	@staticmethod
	def test(iterable, n, start=0, stop=None, step=1):
		"""Run a test comparing enumerate to enumerate2 over 2*n trials

		It is advised to edit this function to make the enumerate for loop more efficient 
		(remove unecessary checks depending on start, stop and step)
		"""
		def doNothing(): x = 0 
		enum1_time = 0
		enum2_time = 0

		for i in range(n):
			t0 = time.process_time()
			for (i, elem) in enumerate(iterable):
				if (start <= i < stop and (i-start)%step==0):
					doNothing()
			t1 = time.process_time()
			enum1_time += t1-t0

			t0 = time.process_time()
			for (i, elem) in enumerate2(iterable, start, stop, step):
				doNothing()
			t1 = time.process_time()
			enum2_time += t1-t0

		for i in range(n): #in reverse order this time, just in case that's causing some mischief
			t0 = time.process_time()
			for (i, elem) in enumerate2(iterable, start, stop, step):
				doNothing()
			t1 = time.process_time()
			enum2_time += t1-t0
			
			t0 = time.process_time()
			for (i, elem) in enumerate(iterable):
				if (start <= i < stop and (i-start)%step==0):
					doNothing()
			t1 = time.process_time()
			enum1_time += t1-t0

		print("Total time for enumerate  loop: {0:.3f}".format(enum1_time))
		print("Total time for enumerate2 loop: {0:.3f}".format(enum2_time))
		return


class multirange:
	"""Extend range() to iterate over a `tuple` of indexes.

	WARNING: At present this is far less efficient than using many for loops.
	It should only be used when the number of required for loops is not known.

    TODO: implement `__multirange_old` in CPython.
	"""
	
	def __init__(self, start, stop=None, step=None):
		"""Create a `multirange` object to iterate over a set of indexes.

		It will increment the final index until increasing by step takes it 
		over its stop point, then will increment the prior index and return the
		final index to its start value before continuing to iterate.

			for (i, j, ...) in multirange(start, stop, step):
				<code to execute in for loop goes here>

		Is equivalent to:
			for i in range(start[0], stop[0], step[0]):
				for j in range(start[1], stop[1], step[1]):
					...
						<code to execute in for loop goes here>
		
		Parameters
		----------
		start : :obj:`tuple` of :obj:`int`
			Tuple of indices to start at.
		stop : :obj:`tuple` of :obj:`int`
			Tuple of indices to stop before.
		step : :obj:`tuple` of :obj:`int`
			Tuple of indices to increment by.
			
		"""
		
		# TYPE CHECKING
		def elementTypeCheck(elem, parameterString):
			"""Raise an appropriate error if <elem> is not of correct type"""
			if not isinstance(elem, int):
				raise TypeError("each index in {0} must be of type '{1}', not type '{2}'".format(parameterString,int,type(elem)) )
			return

		if isinstance(start, tuple):
			self._dim = len([elem for elem in start])
			for elem in start:
				elementTypeCheck(elem, "<start>")
		else:
			raise TypeError("<start> must be of type '{0}', not type '{1}'".format(tuple, type(start)))
		
		if stop == None:
			start, stop = tuple([0 for i in range(self._dim)]), start
		elif isinstance(stop, tuple):
			stop_dim = len([elem for elem in stop])
			if stop_dim != self._dim:
				raise ValueError("<start>, <stop> and <step> must have the same number of elements")
			for elem in stop:
				elementTypeCheck(elem, "<stop>")
		else:
			raise TypeError("<stop> must be of type '{0}', not type '{1}".format(tuple, type(stop)))

		if step == None:
			step = tuple([1 for i in range(self._dim)])
		elif isinstance(step, tuple):
			step_dim = len([elem for elem in step])
			if step_dim != self._dim:
				raise ValueError("<start>, <stop> and <step> must have the same number of elements")
			for elem in step:
				elementTypeCheck(elem, "<step>")
				if elem == 0:
					raise ValueError("each element in <step> must be not be zero")
		else:
			raise TypeError("<step> must be of type '{0}', not type '{1}'".format(tuple, type(step)))

		# ASSIGNING ATTRIBUTES
		self._start = start
		self._stop = stop
		self._step = step
		return

	def __iter__(self):
		start, stop, step = self._start, self._stop, self._step
		ranges = [iter(range(sa,so,se)) for (sa,so,se) in zip(start,stop,step)]
		try:
			indexes = [next(sub_range) for sub_range in ranges] 
		except StopIteration: # At least one range is invalid. Makes multirange() mimic behaviour of range() for invalid ranges
			return
		yield tuple(indexes)

		infimum_range_index = -len(ranges)-1
		range_index = -1
		while range_index > infimum_range_index:
			try:
				new_return_index = next(ranges[range_index])
			except StopIteration:# range has finished iterating
				replacement = iter(range(start[range_index], stop[range_index], step[range_index]))
				ranges[range_index] = replacement
				indexes[range_index] = replacement
				range_index -= 1
			else:
				indexes[range_index] = new_return_index
				yield tuple(indexes)
				range_index = -1
		return





class iterOverIterables:
	def __init__(self, *iters):
		"""Return an object that when iterated over in a for loop, iterates
		over the sequence of iterables. Starting at the first, then when that
		has no more items, iterates over the second one.

			for elem in iterOverIterables(a,b,c):
				<code>

		Is equivalent to:
			for iterable in [a,b,c]:
				for elem in iterable:
					<code>

		Parameters
		----------
		*iters : :obj:`tuple` of iterable

		"""
		for iterable in iters:
			if not isIterable(iterable):
				raise ValueError("must be a sequence of iterables. An object of type '" + str(type(iterable)) + "' is not iterable.")
		self.iters = iters
		return

	def __iter__(self):
		for iterable in self.iters:
			for elem in iterable:
				yield elem
		return


class Wrapper(object):
	"""
	See further below for what I want this for. It's a very niche use case,
	but still very nice to have in my repository.
	
	For intended use in a decorator for a class. In particular, as a base
	class for a local class created in the decorator itself.

	The decorator will assign additional methods/class attributes to the 
	Wrapper, leaving the original class unaffected
	"""
	def __init__(self, wrapped_cls):
		self._wrapped_cls = wrapped_cls
        
	def __getattr__(self, name:str, **kwargs):
		# TODO: this should make a try-except for this class's attribtues
		return getattr(self._wrapped_cls, name, **kwargs)

	def __setattr__(self, name:str, value: any):
		return setattr(self._wrapped_cls, name, value)

	def __repr__(self): 
		return '<wrapped: {} >'.format(repr(self._wrapped_cls)) #To completely hide the fact this is a wrapped class just return repr(self._wrapped_cls)
	
	def __call__(self, *args, **kwargs):
		return self._wrapped_cls(*args, **kwargs)



################################## FUNCTIONS ##################################
def isFloatable(x, acceptNan=False, acceptInf=False):
	"""Return True if `x` is floatable.
	
	Parameters
	----------
	x : any
		Object to check.
	acceptNan : :obj:`bool`, optional
		indicates to return True if `not math.isnan(float(x))`.
	acceptInf : :obj:`bool`, optional
		indicates to return True if `not math.isinf(float(x))`.

	Returns
	-------
	bool
		True if `x` is floatable.
	
	"""
	try: 
		float_x = float(x)
	except ValueError: 
		return False
	else:
		if (not acceptNan) and math.isnan(float_x): return False
		if (not acceptInf) and math.isinf(float_x): return False
	return True

def isCallable(f):
	"""check if a function is callable.
	
	Parameters
	----------
	f : any
		Object to check.

	Returns
	-------
	bool
		True if `f` is callable.

	"""
	try: f.__call__
	except AttributeError: return False
	return True

def isIterable(x):
	"""check if <x> is iterable.
	
	Parameters
	----------
	x : any
		Object to check.
	
	Returns
	-------
	bool
		True if `x` is iterable.
	
	"""
	try:
		(e for e in x) #does iter(x) do the same thing?
		return True
	except TypeError:
		return False

def sign(x):
	"""Return the sign (+1 or -1) of x.
	
	Parameters
	----------
	x : :obj:`int`, :obj:`float`
		Number to check the sign of.
	
	Returns
	-------
	int
		The sign (+1 or -1) of `x`.
	
	"""
	raise DeprecationWarning('use np.sign() instead')
	return int(math.copysign(1, x))

def permuteOptions(listOfLists):
	"""Return a generator object for iterating through all possible permutations of ...
	
	This returns a generator object that iterates all possible lists of values, where the values can be any of their
	respective options.

	Parameters
	----------
	listOfLists : :obj:`list` of :obj:`list`
		Technically, this can be any iterable for which len(listOfLists) is defined.

	Yields
	------
	list
		A list where each element takes a value from the corresponding list at the same index in `listOfLists`.
	
	Examples
	--------
	>>> a = [1,2]
	>>> b = [3,4,5]
	>>> for p in permuteOptions([a,b]): print(p)
	[1,3]
	[1,4]
	[1,5]
	[2,3]
	[2,4]
	[2,5]

	"""
	start = tuple([0 for i in range(len(listOfLists))])
	stop = tuple([len(options) for options in listOfLists])
	for inds in multirange(start, stop):
		yield [options[i] for (i,options) in zip(inds, listOfLists)]
	return

def walkFiles(dir, callback):
    """Walk the files in a directory, calling 'callback' on each file.

    Parameters
    ----------
    dir : str
        Directory to search (relative or absolute)
    callback : FunctionType
        Used as `callback(filepath)` where each file's `filepath` is
        `os.path.join(dir, filepath_relative_to_dir)`.
	
    """
    for root, dirs, files in os.walk(dir):
        for name in files:
            callback(os.path.join(root, name))
    return



################################# DECORATORS ##################################
def print_execution_time(func):
    """decorator, prints the time it takes for the function to execute
	
	Parameters
	----------
	func : function

	Returns
	-------
	function

	"""
    @functools.wraps(func)
    def execution_time_wrapper(*args, **kwargs):
        t0 = time.process_time()
        returnVal = func(*args, **kwargs)
        t1 = time.process_time()
        print("{0} took {1:.3f} seconds to run".format(func.__name__, t1-t0))
        return returnVal
    return execution_time_wrapper

def decorate_cls(*args):
	"""Class decorator for function with parameters

	A way to decorate a class by a function that has parameters.
	A more complete version must have several other methods (including,
	but not limited to,: __setattr__, __hasattr__).

	When I have time I should write out a generic Wrapper class,
	which I could then use in here and simply just inherit from it
	(defining only __init__ and optionally __repr__)
	
	Use case:
	@dec(1,2,3)
	class MyClass:
    	myattr = 1
	
	will set MyClass.myattr2 to [1,2,3]

	Parameters
	----------
	*args
		arguments to the wrapped class?
	
	Returns
	-------
	class
		Not sure what this returns
	
	"""
	class InnerWrapper(Wrapper):
		def __init__(self, wrapped_cls):
			#set class attributes
			super().__init__(wrapped_cls)
			self.myinstanceattr2 = args # instance attributes

		def __repr__(self): 
			return '<decorate_cls.locals.Wrapper wrapped: {} >'.format(repr(self._wrapped_cls)) #To completely hide the fact this is a wrapped class just return repr(self._wrapped_cls)

	setattr(InnerWrapper, "myclassattr", args) # class attributes
	return Wrapper



################### OLD & NON-FUNCTIONING PROTOTYPE FUNCTIONS #################
class __multirange_old:
	"""multirange equivalent to a sequence of for loops

	Note that eventually multirange should share all the methods of range, I 
	just don't think subclassing it will work.
	
	Note that in it's current implementation it is vastly inferior to using a 
	series of nested for loops!

	This version had the ability to iterate over floats instead of just ints!
	Though, it also has a whole lot more pre-flight checks.

	IMPROVEMENTS:
	   * General efficiency
	

    TODO: implement THIS version in CPython. It should be much more efficient.
	"""

	def __init__(self, start, stop=None, step=None, allowFloats=False):
		"""Initiliase a multirange object

		Create a multirange object, this will iterate over a set of indexes.
		It will increment the first index until increasing by step takes it over its
		stop point, then will increment the next index and return the first index to
		its start value before continuing to iterate.

		for (i, j, ...) in multirange(start, stop, step):
			<code to execute in for loop goes here>

		Is equivalent to:
		for i in range(start[0], stop[0], step[0]):
			for j in range(start[1], stop[1], step[1]):
				.
				   .
				      <code to execute in for loop goes here>

		Parameters
		----------
		start : tuple
			tuple of integers, indicating the indicies to start at
		stop : tuple
			tuple of integers, indicating the indicies to stop before
		step : tuple
			tuple of integers, indicating how each index should be incremented
		allowFloat : bool
			flag whether multirange can be over floats (mimicking np.arange) or just over ints
		
		"""
		raise DeprecationWarning("Use multirange instead.")
		# TYPE & POSSIBILITY CHECKING
		if not isinstance(allowFloats, bool):
			raise TypeError("<allowFloats> must be of type '{0}', not type '{1}'".format(bool, type(allowFloats)))
		def elementTypeCheck(elem, parameterString):
			"""Raise an appropriate error if <elem> is not of correct type"""
			if allowFloats:
				if not isinstance(elem, (int, float)):
					raise TypeError("each index in {0} must be of type '{1}' or '{2}', not type '{3}'".format(parameterString,int,float,type(elem)) )
			else: 
				if not isinstance(elem, int):
					raise TypeError("each index in {0} must be of type '{1}', not type '{2}'".format(parameterString,int,type(elem)) )
			return

		if isinstance(start, tuple):
			self._dim = len([elem for elem in start])
			for elem in start:
				elementTypeCheck(elem, "<start>")
		else:
			raise TypeError("<start> must be of type '{0}', not type '{1}'".format(tuple, type(start)))
		
		if stop == None:
			start, stop = tuple([0 for i in range(self._dim)]), start
		elif isinstance(stop, tuple):
			dim = len([elem for elem in stop])
			if dim != self._dim:
				raise ValueError("<start> and <stop> must have the same number of elements")
			for elem in stop:
				elementTypeCheck(elem, "<stop>")
		else:
			raise TypeError("<stop> must be of type '{0}', not type '{1}".format(tuple, type(stop)))

		if step == None:
			step = tuple([1 for i in range(self._dim)])
		elif isinstance(step, tuple):
			dim = len([elem for elem in step])
			if dim != self._dim:
				raise ValueError("<start> and <step> must have the same number of elements")
			for elem in step:
				elementTypeCheck(elem, "<step>")
				if elem == 0:
					raise ValueError("each index in <step> must be non-zero")
		else:
			raise TypeError("<step> must be of type '{0}', not type '{1}'".format(tuple, type(step)))

		# ASSIGNING ATTRIBUTES
		gradients = [sign(stop[i] - start[i]) for i in range(self._dim)]
		self._isiterable = True
		for (i, elem) in enumerate(gradients):
			if elem != sign(step[i]):
				self._isiterable = False #This discretely disallows iteration (mimics the behaviour of range() )
		
		self._start = start
		self._stop = stop
		self._step = step
		self._gradients = tuple(gradients)
		return

	def __len__(self):
		if not self._isiterable:
			return 0
		totals = (math.ceil((self._stop[i] - self._start[i]) // self._step[i]) for i in range(self._dim))
		total = 1
		for elem in totals: 
			total *= elem
		return total

	def __iter__(self):
		#Fun fact: doing 'self._start' etc. is faster than using a local variable 'start' (Actually, the Hypothesis test was inconclusive)
		indexes = list(self._start)
		iter_range = range(self._dim-1, 0, -1)
		for i in range(len(self)):
			yield tuple(indexes)
			indexes[-1] += self._step[-1]
			for j in iter_range:
				if self._gradients[j] == 1:
					if indexes[j] < self._stop[j]: break
				else:
					if indexes[j] > self._stop[j]: break
				indexes[j] = self._start[j]
				indexes[j-1] += self._step[j-1]
		return


class __multirange2(multirange):
	"""
	The recursive solution may be along the lines of this.
	But, this algorithm doesn't work/isn't finished
	"""

	def __iter__(self):
		inds = list(self._start)
		yield tuple(inds)
		while True:
			yield tuple(self.nextInds(inds, -1))

	def nextInds(self, inds, i):
		print(inds, i)
		if i <= -len(inds): return None
		for j in range(inds[i], self._stop[i], self._step[i]):
			N = self.nextInds(inds, i-1)
			print(N)
			if N == None:
				inds[i] = j
			else:
				inds[i-1] = self._start[i-1]
				return N


def __isFloatable_old(string): 
	"""Check if `string` is floatable

	Check a string to see whether it can be converted into a float.
	NOTE: this returns False for "NaN" and "Inf"
	NOTE: this returns False for strings such as "1e10" which can be floated
	
	Parameters
	----------
	string : str
		string to check

	Returns
	-------
	bool
		True if `string` can be converted, False if not.
	
	"""
	raise DeprecationWarning("Inefficient method, see isFloatable() for the better version")
	# (Upchurch, 2009) - Idea for splitting string, checking either side of decimal point
	if string == "":
		return False
	
	# Negative sign check
	negIndex = string.find("-")
	if negIndex != -1:
		if string[:negIndex].lstrip() != "":
			return False
		if string.find("-", negIndex+1) != -1:
			return False
		string = string[negIndex+1:]

	# Digits on either side of a '.'
	part_list = string.split(".")
	if len(part_list) > 2:
		return False
	for side in part_list:
		if not side.isdigit():
			return False
	return True

def __permuteOptions_new(iterOfIters):
	"""Return a generator object for iterating through all possible permutations of an iterable of iterables
		
	iterOfIters is of the form:
		[ value1, value2, value3, ...]
	where
		value1 = [option1, option2, ...]

	This returns a generator object that iterates all possible lists of values, where the values can
	be any of their respective options

	Parameters
	----------
	iterOfIters : iterable
		Iterable of iterables.
	
	Yields
	------
	list
		a permutation of the given options
	
	"""
	#I use a modified version in simpleUncertainty that only uses objects that have a len() attribute,
	#That one is more efficient as it doesn't have to loop the first time
	raise NotImplementedError("This does not work as intended - it requires indexing... What I need instead is a multienumerate()")
	start = []
	stop = []
	if not isIterable(iterOfIters):
		raise ValueError("<iterOfIters> must be iterable. An object of type '" + str(type(iterOfIters)) + "' is not.")
	for options in iterOfIters:
		start.append(0)
		if not isIterable(options):
			raise ValueError("each element of <iterOfIters> must be iterable. An object of type '" + str(type(options)) + "' is not.")
		try:
			stop.append(len(options))
		except AttributeError:
			length = 0
			for elem in options: 
				length += 1
			stop.append(length)
	for inds in multirange(start, stop):
		raise NotImplementedError("This does not work as intended - it requires indexing... What I need instead is a multienumerate()")
		yield [options[i] for (i,options) in zip(inds, listOfLists)]
	return
