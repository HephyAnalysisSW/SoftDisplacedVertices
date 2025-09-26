import FWCore.ParameterSet.Config as cms
from Configuration.Generator.Pythia8CommonSettings_cfi import *
from Configuration.Generator.MCTunes2017.PythiaCP5Settings_cfi import *
from Configuration.Generator.PSweightsPythia.PythiaPSweightsSettings_cfi import *

mStop = STOPMASS
mLSP = LSPMASS
ctau = CTAUVALUE
ctaustr = "{:.1f}".format(ctau).replace('.','p')

hBarCinGeVmm = 1.973269788e-13
gevWidth = hBarCinGeVmm / ctau

FLAVOR = 'stop'
PROCESS_FILE = 'SimG4Core/CustomPhysics/data/stophadronProcessList.txt'
PARTICLE_FILE = 'Configuration/Generator/data/particles_%s_%d_GeV.txt'  % (FLAVOR, int(mStop))
SLHA_FILE ='Configuration/Generator/data/SUSY/LLStop/LL_%s_%d_Neutralino_%d_CTau_%s_SLHA.spc' % (FLAVOR, int(mStop), int(mLSP), ctaustr)
PDT_FILE = 'Configuration/Generator/data/hscppythiapdt%s%d.tbl'  % (FLAVOR, int(mStop))
USE_REGGE = False

#Link to datacards:
#https://github.com/CMS-SUS-XPAG/GenLHEfiles/tree/master/GridpackWorkflow/production/SMS-StopStop/templatecards

model = "T2tt_dM-10to80"

def matchParams(mass):
  if mass>99 and mass<199: return 62., 0.498
  elif mass<299: return 62., 0.361
  elif mass<399: return 62., 0.302
  elif mass<499: return 64., 0.275
  elif mass<599: return 64., 0.254
  elif mass<1299: return 68., 0.237
  elif mass<1801: return 70., 0.243

qcut, tru_eff = matchParams(mStop)
#wgt = 50/tru_eff #NOTE: config weight

basePythiaParameters = cms.PSet(
    pythia8CommonSettingsBlock,
    pythia8CP5SettingsBlock,
    pythia8PSweightsSettingsBlock,
    JetMatchingParameters = cms.vstring(
      'JetMatching:setMad = off',
      'JetMatching:scheme = 1',
      'JetMatching:merge = on',
      'JetMatching:jetAlgorithm = 2',
      'JetMatching:etaJetMax = 5.',
      'JetMatching:coneRadius = 1.',
      'JetMatching:slowJetPower = 1',
      'JetMatching:qCut = %.0f' % qcut, #this is the actual merging scale
      'JetMatching:nQmatch = 5', #4 corresponds to 4-flavour scheme (no matching of b-quarks), 5 for 5-flavour scheme
      'JetMatching:nJetMax = 2', #number of partons in born matrix element for highest multiplicity
      'JetMatching:doShowerKt = off', #off for MLM matching, turn on for shower-kT matching
      '6:m0 = 172.5',
      '24:mMin = 0.1',
      'Check:abortIfVeto = on',
    ),
    parameterSets = cms.vstring('pythia8CommonSettings',
                                'pythia8CP5Settings',
                                'pythia8PSweightsSettings',
                                'JetMatchingParameters'
    )
    )

basePythiaParameters.pythia8CommonSettings.extend(['1000006:tau0 = %e' % ctau])
basePythiaParameters.pythia8CommonSettings.extend(['ParticleDecays:tau0Max = 1000.1'])
basePythiaParameters.pythia8CommonSettings.extend(['LesHouches:setLifetime = 2'])

basePythiaParameters.pythia8CommonSettings.extend(['RHadrons:allow  = on'])
basePythiaParameters.pythia8CommonSettings.extend(['RHadrons:allowDecay = on'])
basePythiaParameters.pythia8CommonSettings.extend(['RHadrons:setMasses = on'])

generator = cms.EDFilter("Pythia8ConcurrentHadronizerFilter",
  maxEventsToPrint = cms.untracked.int32(1),
  pythiaPylistVerbosity = cms.untracked.int32(1),
  filterEfficiency = cms.untracked.double(1.0),
  pythiaHepMCVerbosity = cms.untracked.bool(False),
  comEnergy = cms.double(13000.),
  PythiaParameters = basePythiaParameters,
  SLHAFileForPythia8 = cms.string('%s' % SLHA_FILE), 
  ConfigDescription = cms.string('%s_%i_%i' % (model, mStop, mLSP)),
  #ConfigWeight = cms.double(wgt),
)

generator.hscpFlavor = cms.untracked.string(FLAVOR)
generator.massPoint = cms.untracked.int32(int(mStop))
generator.particleFile = cms.untracked.string(PARTICLE_FILE)
generator.slhaFile = cms.untracked.string(SLHA_FILE)
generator.processFile = cms.untracked.string(PROCESS_FILE)
generator.pdtFile = cms.FileInPath(PDT_FILE)
generator.useregge = cms.bool(USE_REGGE)

#     Filter setup
# ------------------------
# https://github.com/cms-sw/cmssw/blob/CMSSW_8_0_X/PhysicsTools/HepMCCandAlgos/python/genParticles_cfi.py
tmpGenParticles = cms.EDProducer("GenParticleProducer",
saveBarCodes = cms.untracked.bool(True),
src = cms.InputTag("generator","unsmeared"),
abortOnUnknownPDGCode = cms.untracked.bool(False)
)

# https://github.com/cms-sw/cmssw/blob/CMSSW_8_0_X/RecoJets/Configuration/python/GenJetParticles_cff.py
# https://github.com/cms-sw/cmssw/blob/CMSSW_8_0_X/RecoMET/Configuration/python/GenMETParticles_cff.py
tmpGenParticlesForJetsNoNu = cms.EDProducer("InputGenJetsParticleSelector",
src = cms.InputTag("tmpGenParticles"),
ignoreParticleIDs = cms.vuint32(
     1000022,
     1000012, 1000014, 1000016,
     2000012, 2000014, 2000016,
     1000039, 5100039,
     4000012, 4000014, 4000016,
     9900012, 9900014, 9900016,
     39,12,14,16),
partonicFinalState = cms.bool(False),
excludeResonances = cms.bool(False),
excludeFromResonancePids = cms.vuint32(12, 13, 14, 16),
tausAsJets = cms.bool(False)
)

# https://github.com/cms-sw/cmssw/blob/CMSSW_8_0_X/RecoJets/JetProducers/python/AnomalousCellParameters_cfi.py
AnomalousCellParameters = cms.PSet(
maxBadEcalCells         = cms.uint32(9999999),
maxRecoveredEcalCells   = cms.uint32(9999999),
maxProblematicEcalCells = cms.uint32(9999999),
maxBadHcalCells         = cms.uint32(9999999),
maxRecoveredHcalCells   = cms.uint32(9999999),
maxProblematicHcalCells = cms.uint32(9999999)
)

# https://github.com/cms-sw/cmssw/blob/CMSSW_8_0_X/RecoJets/JetProducers/python/GenJetParameters_cfi.py
GenJetParameters = cms.PSet(
src            = cms.InputTag("tmpGenParticlesForJetsNoNu"),
srcPVs         = cms.InputTag(''),
jetType        = cms.string('GenJet'),
jetPtMin       = cms.double(3.0),
inputEtMin     = cms.double(0.0),
inputEMin      = cms.double(0.0),
doPVCorrection = cms.bool(False),
# pileup with offset correction
doPUOffsetCorr = cms.bool(False),
   # if pileup is false, these are not read:
   nSigmaPU = cms.double(1.0),
   radiusPU = cms.double(0.5),
# fastjet-style pileup
doAreaFastjet  = cms.bool(False),
doRhoFastjet   = cms.bool(False),
  # if doPU is false, these are not read:
  Active_Area_Repeats = cms.int32(5),
  GhostArea = cms.double(0.01),
  Ghost_EtaMax = cms.double(6.0),
Rho_EtaMax = cms.double(4.5),
useDeterministicSeed= cms.bool( True ),
minSeed             = cms.uint32( 14327 )
)

# https://github.com/cms-sw/cmssw/blob/CMSSW_8_0_X/RecoJets/JetProducers/python/ak4GenJets_cfi.py
tmpAk4GenJetsNoNu = cms.EDProducer(
"FastjetJetProducer",
GenJetParameters,
AnomalousCellParameters,
jetAlgorithm = cms.string("AntiKt"),
rParam       = cms.double(0.4)
)

genHTFilter = cms.EDFilter("GenHTFilter",
src = cms.InputTag("tmpAk4GenJetsNoNu"), #GenJet collection as input
jetPtCut = cms.double(30.0), #GenJet pT cut for HT
jetEtaCut = cms.double(5.0), #GenJet eta cut for HT
genHTcut = cms.double(200.0) #genHT cut
)


tmpGenMetTrue = cms.EDProducer("GenMETProducer",
src = cms.InputTag("tmpGenParticlesForJetsNoNu"),
onlyFiducialParticles = cms.bool(False), ## Use only fiducial GenParticles
globalThreshold = cms.double(0.0), ## Global Threshold for input objects
usePt   = cms.bool(True), ## using Pt instead Et
applyFiducialThresholdForFractions   = cms.bool(False),
)

genMETfilter1 = cms.EDFilter("CandViewSelector",
 src = cms.InputTag("tmpGenMetTrue"),
 cut = cms.string("pt > 100")
)

genMETfilter2 = cms.EDFilter("CandViewCountFilter",
src = cms.InputTag("genMETfilter1"),
minNumber = cms.uint32(1),
)


ProductionFilterSequence = cms.Sequence(generator*
                                    tmpGenParticles * tmpGenParticlesForJetsNoNu *
                                    tmpAk4GenJetsNoNu * genHTFilter *
                                    tmpGenMetTrue * genMETfilter1 * genMETfilter2
)

