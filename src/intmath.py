"""A set of functions for doing math with integers."""



################################### MODULES ###################################
import math



################################## FUNCTIONS ##################################
def factors(a): 
    """Return a sorted list of the factors of `a`."""
    fact_list = []
    for x in range(1, round(math.sqrt(a)) + 1):
        if a % x == 0:
            fact_list.append(x)
    return fact_list

def primes(n, primeList=None):
    """Return a list of the primes <= `n`. 
    
    Parameters
    ----------
    n : int
        Largest number to check for being prime
    primeList : :obj:`list` of :obj:`int`, optional
        Can specify an already calculated (ordered) list of primes to extend it
        instead of starting from scratch.
    
    Returns
    -------
    :obj:`list` of :obj:`int`

    Notes
    -----
    I haven't verified this functions behaviour. It needs to be tested.

    """
    # Initial primes list
    if primeList != None: 
        primes = primeList[:]
        while primes[-1] > n:
            primes.pop(-1)
    else:
        if n <= 0: return []
        if n == 1: return [2]
        else: primes = [2, 3]

    # Adding primes to list
    for i in range(primes[-1]+2, n+1, 2):
        lastPrimeToCheck = math.floor( math.sqrt(i) ) + 1
        isPrime = True
        for p in primes:
            if p > lastPrimeToCheck: break
            if i % p == 0: 
                isPrime = False
                break
        if isPrime: primes.append(i)
        

        """ Original: Likely less efficient, as em_find involves superfluous steps (idea was to not have the p> check every time and loop through a set loop)
        primesToCheck = primes[:primes.em_find(math.floor( math.sqrt(i) ) + 1)] 
        isPrime = True
        for p in primesToCheck: 
            if i % p == 0: 
                isPrime = False
                break
        if isPrime: primes.append(i)
        """

    return primes

def modulo(x, m=None, range_=None):
    """Return x modulo m. 
    
    Parameters
    ----------
    x : int
    m : int
    range_ : :obj:`tuple` of :obj:`int`, optional
        If specified, `range` takes the form `(lower,upper)` and results in `x`
        being placed in that range, and being x (modulo upper-lower). `m` is
        ignored if this is specified.
    
    Results
    -------
    int

    Notes
    -----
    Thought process for the logic: start from lower, or upper, then count the
    number of elements (include going down as negative) then that is the number
    (mod range). This is then put back into the range by + lower
    modulus(-6, (1, 5)) = 4 because:
        `-6 -5 -4 -3 -2 -1 0 1 2 3 4 5`  (mod range) is
        ` 4  5  1  2  3  4 5 1 2 3 4 5`
    
    """
    if range_ == None:
        y = x % m
        if y<0: y += m
        return y

    else:
        lower, upper = range_[0], range_[1]
        if lower > upper: raise ValueError("range_[0] must be < range_[1]")
        m = upper - lower + 1
        return (x - lower) % m + lower
    return
