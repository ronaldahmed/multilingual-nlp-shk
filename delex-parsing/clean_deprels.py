import sys

blocks = open(sys.argv[1], 'r').read().strip('\n').split('\n\n')

for bl in blocks:
  for line in bl.split('\n'):
    if line[0]=="#":
      print(line)
      continue
    fields = line.split('\t')
    fields[7] = fields[7].split(":")[0]
    print("\t".join(fields))
  print()
  