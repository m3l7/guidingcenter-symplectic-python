from config import Config
from particle import Particle
from particleUtils import printToFile, writeHeaderToFile
import sys
import getopt


# configuration
config = Config()

# parse command line
outFile = config.outFile
try:
    opts, args = getopt.getopt(sys.argv[1:], "o:")
except getopt.GetoptError:
    print("Usage python3 main.py -o outFile")
    sys.exit(2)
for opt, arg in opts:
    if opt == "-o":
        outFile = arg

# create a particle
particle = Particle(config, config.z0, config.p0, config.z1, config.p1)
particle.initialize(config.initializationType)
for i in range(config.initBackwardIterations):
    particle.backwardInitializationIteration(config.initBackWardOrder)

print("Saving to {}".format(outFile))
print("Time step: ", config.h)
print("Initialization: ")
print("z_init: " + str(particle.z0))
print("z0: " + str(particle.z1))
print("mu_0: " + str(config.mu))

# open output file
out = open(outFile, "w+")
writeHeaderToFile(out)
printToFile(0, config, particle, out, timestep0=True)
printToFile(1, config, particle, out)
out.close()
out = open(outFile, "a+")

#  ******
# MAIN LOOP
#  ******
for t in range(2, config.nsteps):
    # PRINT TO SCREEN EVERY N STEPS
    if (t % config.printTimestepMult) == 0:
        print("Timestep " + str(t))

    particle.stepForward(t)

    # PRINT TO FILE
    if (t % config.fileTimestepMult) == 0:
        printToFile(t, config, particle, out)

    # EXIT IF THE ERROR IS TOO HIGH
    if config.exitOnError:
        if abs(particle.dE1) > config.errorThreshold:
            print("Timestep: " + str(t) + "\tError too high! Exiting.")
            break
