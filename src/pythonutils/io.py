"""IO operations module"""



################################### MODULES ###################################
import os



################################## CLASSES ####################################
class OpenReadWrite:
	def __init__(self, filename, readkwargs = None, writekwargs = None, _debugMode = False):
		"""Open an empty file for writing to, and a file to read from.

		Parameters
		---------
		filename : str
			path to file
		readkwargs : dict, optional
			Extra arguments to `open` of the readFile
		writekwargs : dict, optional
			Extra arguments to `open` of the writeFile
		_debugMode : bool, optional
			Never change the source file `<filename>`, and always leave the
			result (complete or partial) as `<filename>.new`.

		Examples
		--------
		Append 'I added this sentence.' to every line in a file.

		>>> with OpenReadWrite('myfile.txt') as (readFile, writeFile):
		... 	for line in readFile:
		... 		end = '\\n' if line[-1] == '\\n' else ''
		... 		line = line.strip('\\n')
		... 		line += 'I added this sentence.' + end
		... 		writeFile.write(line)

		"""
		self._readFile = None
		self._readName = filename
		self._writeFile = None
		self._writeName = filename + '.new'
		self._readkwargs = readkwargs or {} # default {}
		self._writekwargs = writekwargs or {} # default {}
		self._debugMode = _debugMode
		return

	def __enter__(self):
		if not self._debugMode and os.path.exists(self._writeName):
			raise FileExistsError('{0} already exists, and is required to not exist to operate on {1}'.format(self._writeName, self._readName))
		self._readFile = open(self._readName, 'r', **self._readkwargs)
		self._writeFile = open(self._writeName, 'w', **self._writekwargs)
		return (self._readFile, self._writeFile)

	def __exit__(self, exc_type, exc_value, exc_traceback):
		self._readFile.close()
		self._writeFile.close()
		if self._debugMode:
			if exc_type is None:
				print("[DEBUG MODE] No Errors in {}".format(self._readName))
			else:
				print("[DEBUG MODE] Error occured in handling file {}".format(self._readName))
		else:
			if exc_type is None:
				os.remove(self._readName)
				os.rename(self._writeName, self._readName)
			else:
				print("Error in handling file, the partial result is available as {}".format(self._writeName))
		return

class OpenWithContext:
	def __init__(self, filename, nAbove = 0, nBelow = 0, **kwargs):
		"""Open a file such that iterating line-by-line is done with context
		lines above and below. Can only open files in 'r' mode.

		Note: only affects `for line in file` statements. Everything else is
		as per a normal `open(filename, 'r')`.
		
		Parameters
		----------
		filename : str
			Path to the file
		nAbove : int
			Number of lines above to include as context.
		nBelow : int
			Number of lines below to include as context.
		**kwargs : dict, optional
			Optional keyword arguments to `open`

		Notes
		-----
		The full context as a single string can be compiled as:
			''.join(aboveLines) + line + ''.join(belowLines)

		Examples
		--------
		Opening a 6 line file with 3 context lines above and 2 below.

		>>> with OpenWithContext(myfilename, 3, 2) as file:
		... 	for i, (aboveLines, line, belowLines) in enumerate(file):
		... 		print(i, len(aboveLines), len(belowLines))
		0 0 2
		1 1 2
		2 2 2
		3 3 2
		4 3 1
		5 3 0

		"""
		if not isinstance(nAbove, int):
			raise TypeError('nAbove must be an int, not {}'.format(type(nAbove)))
		if not isinstance(nBelow, int):
			raise TypeError('nBelow must be an int, not {}'.format(type(nBelow)))
		self._file = open(filename, 'r', **kwargs)
		self._nAbove = nAbove
		self._nBelow = nBelow
		return

	def __iter__(self):
		"""
		Yields
		------
		tuple[list[str], line, list[str]]
		
		"""
		line = self._file.readline()

		# Get below context lines TODO: cleanup
		above = []
		below = []
		if self._nBelow > 0:
			for i, contextLine in enumerate(self._file):
				below.append(contextLine)
				if i+1 >= self._nBelow: break
		yield (above.copy(), line, below.copy())

		# Operate on lines
		for lastContextLine in self._file:
			above.append(line)
			if len(above) > self._nAbove: del above[0]
			below.append(lastContextLine)
			line = below.pop(0)
			yield (above.copy(), line, below.copy())

		for _ in range(len(below)):
			above.append(line)
			if len(above) > self._nAbove: del above[0]
			line = below.pop(0)
			yield (above.copy(), line, below.copy())
		return

	## INHERITED METHODS ##
	def __getattr__(self, __name: str, *args, **kwargs):
		return getattr(self._file, __name, *args, **kwargs)
	
	def __enter__(self): return self
	def __exit__(self, *exc): self._file.close()

class OpenReadWriteWithContext(OpenReadWrite):
	def __init__(self, filename, nAbove = 0, nBelow = 0, **kwargs):
		"""OpenReadWrite but with OpenWithContext for the read file.
		
		Notes
		-----
		Using the `opener` of `open` may work better.

		See Also
		--------
		OpenReadWrite
		OpenWithContext

		"""
		super().__init__(filename, **kwargs)
		self._nAbove = nAbove
		self._nBelow = nBelow
		return
	
	def __enter__(self):
		super().__enter__()
		self._readFile.close()
		self._readFile = OpenWithContext(self._readName, nAbove = self._nAbove, nBelow = self._nBelow, **self._readkwargs)
		return (self._readFile, self._writeFile)



################################## FUNCTIONS ##################################
def walkFiles(dir, callback):
	"""Walk the files in a directory, calling 'callback' on each file.

	Parameters
	----------
	dir : str
		Directory to search (relative or absolute)
	callback : FunctionType
		Used as `callback(filepath)` where each file's `filepath` is
		`os.path.join(dir, filepath_relative_to_dir)`. Note that these
		are not absolute file paths, they are relative but also include
		the dir!
	
	"""
	for root, dirs, files in os.walk(dir):
		for name in files:
			callback(os.path.join(root, name))
	return

def numLinesInFile(fileObject):
	"""Get Number of lines in a file.
	
	Parameters
	----------
	fileObject : ?
		As returned by open()
	"""
	for i, _ in enumerate(fileObject): pass
	try:
		fileLen = i + 1
	except UnboundLocalError:
		fileLen = 0
	fileObject.seek(0)
	return fileLen