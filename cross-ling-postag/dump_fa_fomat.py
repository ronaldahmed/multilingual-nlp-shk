import sys

source = open(sys.argv[1])
target = open(sys.argv[2])

for ls in source:
	lt = target.readline()
	ls = ls.strip('\n')
	lt = lt.strip('\n')

	print("%s ||| %s" % (ls,lt))

