# For STOP request
#for m in 400 500 600 700 800 900 1000 1100 1200 1300 1400
#do
#  python frag.py -m ${m} -d 25 -c 0.2 -n 5000
#  python frag.py -m ${m} -d 20 -c 2 -n 5000
#  python frag.py -m ${m} -d 15 -c 20 -n 5000
#  python frag.py -m ${m} -d 12 -c 200 -n 5000
#  python frag.py -m ${m} -d 20 -c 0.2 -n 5000
#  python frag.py -m ${m} -d 15 -c 2 -n 5000
#  python frag.py -m ${m} -d 12 -c 20 -n 5000
#done

# For C1N2 request
for m in 200 300 400 500 600
do
  for dm in 12 15 20 25
  do
    for ct in 0.2 2 20 200
    do
      python frag.py -m ${m} -d ${dm} -c ${ct} -n 5000
    done
  done
done
