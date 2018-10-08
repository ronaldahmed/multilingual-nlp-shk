NPFL120 - HOMEWORK 01

README
================================
Main file: tasks.py

usage: tasks.py [-h] [--task TASK] [--wals WALS] [--genus GENUS]
                [--family FAMILY]

Run IR system w specific configuration.

optional arguments:
  -h, --help            show this help message and exit
  --task TASK, -t TASK  Task id
  --wals WALS, -w WALS  WALS code
  --genus GENUS, -g GENUS
                        Genus code
  --family FAMILY, -f FAMILY
                        Family name


Examples showing how to run the code for the 3 tasks:

* Task 1:
python3 tasks.py -t 1 -w cze


* Task 2:
python3 tasks.py -t 2 -g Slavic


* Task 3:

python3 tasks.py -t 3 -f Indo-European 

python3 tasks.py -t 3 -g Slavic