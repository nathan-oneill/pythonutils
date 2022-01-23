"""IO operations module"""



################################### MODULES ###################################
import os



################################## CLASSES ####################################
class OpenReadWrite:
	def __init__(self, filename):
		"""Open an empty file for writing to, and a file to read from.

		Parameters
		---------
		filename : str
			path to file

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
		self.filename = filename
		self.readFile = None
		self.writeFile = None
		return

	def __enter__(self):
		readName = self.filename + '.bak'
		
		if os.path.exists(readName):
			raise FileExistsError('{0}.bak already exists, and is required to not exist to operate on {0}'.format(self.filename))
		os.rename(self.filename, readName)

		self.readFile = open(readName, 'r')
		self.writeFile = open(self.filename, 'w')

		return (self.readFile, self.writeFile)

	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.readFile.close()
		self.writeFile.close()
		if exc_type is None:
			os.remove(self.filename + '.bak')
		else:
			print("Error in file handling, the original file is available as '{}.bak'".format(self.filename))
		return



################################## FUNCTIONS ##################################
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