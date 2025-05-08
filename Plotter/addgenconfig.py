import yaml
import os
import click

@click.command()
@click.argument('filename')
def addgensel(filename):

  with open(filename, 'r') as f:
      c = yaml.safe_load(f)
  
  newc = c.copy()
  
  sels = {
      'SDVSecVtx': "(SDVSecVtx_matchedLLPnDau_bydau>1)",
      'SDVTrack': "SDVTrack_LLPIdx>=0",
      }
  
  for geno in sels:
  
    for o in newc['objects']:
      if geno in o:
        if not ("selections" in newc['objects'][o]):
          continue
        for s in newc['objects'][o]["selections"]:
          if newc['objects'][o]["selections"][s] is None:
            newc['objects'][o]["selections"][s] = sels[geno]
          else:
            newc['objects'][o]["selections"][s] += " && {}".format(sels[geno])
  
  fn_new = filename.replace(".yaml","sig.yaml")
  assert not os.path.exists(fn_new), "File {} already exists!".format(fn_new)

  with open(fn_new, 'w') as file:
    yaml.dump(newc, file)

if __name__ == "__main__":
  addgensel()
