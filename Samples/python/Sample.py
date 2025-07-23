# This is a class that include necessary information of a sample.
import os
from XRootD import client
from XRootD.client.flags import DirListFlags, OpenFlags, MkDirFlags, QueryCode

class Sample:
  def __init__(self, name, xsec, filter_eff=1):
    self.name = name
    self.xsec = xsec
    self.filter_eff = filter_eff
    self.dirs = {}
    self.eosdirs = {}
    self.dataset = {}
    self.dataset_instance = {}
    self.nevents = {}

  def setxsec(self,xsec):
    self.xsec = xsec

  def setNEvents(self,label,nevt):
    assert label not in self.nevents
    self.nevents[label] = nevt

  def getNEvents(self,label):
    if not label in self.nevents:
      return -1
    return self.nevents[label]

  def setEOSDirs(self, label, dirs):
    assert label not in self.eosdirs
    self.eosdirs[label] = dirs

  def setDirs(self, label, dirs):
    assert label not in self.dirs
    self.dirs[label] = dirs

  def setDataset(self, label, dataset, instance):
    assert label not in self.dataset
    assert label not in self.dataset_instance
    self.dataset[label] = dataset
    self.dataset_instance[label] = instance

  def getFileList(self, label, namebase):
    #FIXME: Make this work for DBS
    assert (label in self.dirs) or (label in self.eosdirs)
    fileNames = []
    if label in self.dirs:
      for root, dirs, files in os.walk(self.dirs[label]):
        for ifile in files:
          if (namebase in ifile and ifile.endswith('.root')):
            fileNames.append(os.path.join(root,ifile))
    elif label in self.eosdirs:
      redirector = 'root://eos.grid.vbc.ac.at/'
      myclient = client.FileSystem(redirector)
      dirstack = [self.eosdirs[label]]
      while len(dirstack)>0:
        d_temp = dirstack.pop(0)
        if d_temp[-1] != '/':
          d_temp += '/'
        status, listing = myclient.dirlist(d_temp, DirListFlags.STAT)
        for ele in listing:
          if ele.statinfo.flags == client.flags.StatInfoFlags.IS_DIR:
            dirstack.append(d_temp+ele.name)
          elif (namebase in ele.name) and (ele.name.endswith('.root')):
            fileNames.append(redirector+d_temp+ele.name)
    else:
      print("No files found for {}!".format(self.name))

    return fileNames

  def getFileDirs(self,label):
    return self.dirs[label]


  # Make sure getNEvents are getting the number of events in the full dataset before using this method. Otherwise it will be very wrong
  #def getLumiWeights(self, lumi):
  #  if self.getNEvents()==-1:
  #    print("WARNING! Number of events are not available!")
  #    return 1
  #  return lumi*self.xsec/self.getNEvents()
