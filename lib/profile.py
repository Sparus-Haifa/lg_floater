import os.path
import gsw
import lib.logger as logger
import numpy as np

class Profile:
    def __init__(self, filepath, log):
        self.filepath = filepath
        self.log = log
        self.table = []
        self.__loadfile()
        self.log.write("Profile class was initialized successfully\n")

    def __loadfile(self):
        #fields: pressure, temp, salinity
        print("attempting to load profile: " + self .filepath)
        self.log.write("attempting to load profile: " + self.filepath + "\n")
        for line in open(self .filepath, 'r').readlines():
            fields = line.strip().split()
            fields = [float(i) for i in fields] # convert to floats
            fields.append(self.__getdensity(fields))
            self.log.write(str(fields) + "\n")
            self.table.append(fields)


    def __getdensity(self, fields):
        if (len(fields) != 3):
            self.log.write("invalid profile line: " + fields)
            return
        else:
            p = fields[0]
            t = fields[1]
            SA = fields[2]
            CT = gsw.CT_from_t(SA, t, p)
            return gsw.density.rho(SA, CT, p)


if __name__ == "__main__":
    log = logger.Logger()
    try:
        profile = Profile("../cfg/profile.txt", log)
    except Exception as ex:
        print("-E- failed to init Profile")
        print(str(ex))
        exit()