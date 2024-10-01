import os, sys, glob
import getopt, datetime
import shutil

##################################################
##### FUNCTION DEFINITIONS FOR EVENT NUMBER ######
##################################################

def save_value_to_file(value):
    with open("config.txt", "w") as file:
        file.write(str(value))

def read_value_from_file():
    try:
        with open("config.txt", "r") as file:
            return int(file.read().strip())
    except IOError:
        save_value_to_file(1)
        return 1

##################################################

########## setup

home = os.getcwd()
dirtemplates = home + "/templates"
dirdrivers = home + "/drivers"
#wdir = home + "/simulations"
#wdir = "/scratch/ang.li/GenProduction_24bodystop_log"
wdir = "/scratch/ang.li/GenProduction_2017STOP"

########## options

opts, args = getopt.getopt(sys.argv[1:], "rbm:l:c:n:y:", ["reset", "bash", "llpmass=", "lspmass=", "ctau=", "nevents=", "year="])

reset = False
bash = False
llpmass = 600.
lspmass = 588.
ctau = 200.  # in mm!
nevents = 5000
year = 2018

for opt, arg in opts:
    if opt in ("-r", "--reset"):
        reset = True
    if opt in ("-b", "--bash"):
        bash = True
    if opt in ("-m", "--llpmass"):
        llpmass = float(arg)
    if opt in ("-l", "--lspmass"):
        lspmass = float(arg)
    if opt in ("-c", "--ctau"):
        ctau = float(arg)
    if opt in ("-n", "--nevents"):
        nevents = int(arg)
    if opt in ("-y", "--year"):
        year = int(arg)

if reset:
    save_value_to_file(1)
firstEvent = read_value_from_file()
save_value_to_file(firstEvent + nevents)

#drivers_t = dirdrivers + "/C1N2_{}_{}_{}_{}".format(llpmass, lspmass, ctau, nevents)
drivers_t = dirdrivers + "/STOP_{}_{}_{}_{}_{}".format(llpmass, lspmass, ctau, nevents, year)
#drivers_t = dirdrivers + "/N2N3_{}_{}_{}_{}".format(n2n3mass, lspmass, ctau, nevents)

if not os.path.exists(drivers_t):
    exit("No existing drivers for mass configuration, create drivers first")

########## prepare working directory

if not os.path.exists(wdir):
    os.mkdir(wdir)
os.chdir(wdir)

wdirs = glob.glob("run*")

ndirs = [0]
for wdir in wdirs:
    ndirs.append(int(wdir[3:]))
lastndir = max(ndirs)

thiswdir = "run{}".format(lastndir + 1)

os.mkdir(thiswdir)
os.chdir(thiswdir)
os.environ["RUN_NUMBER"] = thiswdir
os.environ["FIRST_EVENT"] = str(firstEvent)

jobfile_t = dirtemplates + "/job_template_{}.sh".format(year)
jobfile = "job.sh"

#fragmentfile_t = dirtemplates + "/SMS_C1N2-fragment_template.py"
fragmentfile_t = dirtemplates + "/STOP-fragment_template.py"
#fragmentfile_t = dirtemplates + "/SMS_N2N3-fragment_template.py"
fragmentfile = "fragment.py"

random_t = dirtemplates + "/random.py"
random = "random.py"

drivers = "drivers"

shutil.copyfile(random_t, random)

llpStr = str(int(llpmass)) if int(llpmass) == llpmass else str(llpmass).replace(".","p")
lspStr = str(int(lspmass)) if int(lspmass) == lspmass else str(lspmass).replace(".","p")
ctauStr = str(int(ctau)) if int(ctau) == ctau else str(ctau).replace(".","p")

shutil.copyfile(jobfile_t, jobfile)
#os.system('sed -i "s|PROCESS|' + "C1N2" + '|g" ' + jobfile)
os.system('sed -i "s|PROCESS|' + "STOP" + '|g" ' + jobfile)
#os.system('sed -i "s|PROCESS|' + "N2N3" + '|g" ' + jobfile)
os.system('sed -i "s|LLPMASS|' + llpStr + '|g" ' + jobfile)
os.system('sed -i "s|LSPMASS|' + lspStr + '|g" ' + jobfile)
os.system('sed -i "s|CTAUVALUE|' + ctauStr + '|g" ' + jobfile)
os.system('sed -i "s|EVENTCOUNT|' + str(nevents) + '|g" ' + jobfile)

shutil.copytree(drivers_t, drivers)

########## submit jobs

if not bash:
    os.system("sbatch job.sh")

else:
    os.system("bash job.sh")
