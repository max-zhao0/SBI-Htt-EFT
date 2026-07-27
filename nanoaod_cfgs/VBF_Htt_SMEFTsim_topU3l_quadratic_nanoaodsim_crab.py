from CRABClient.UserUtilities import config
config = config()

config.General.requestName     = 'VBF_Htt_SMEFTsim_topU3l_quadratic_nanoaodsim_5mevents'
config.General.workArea        = 'crab_jobs'
config.General.transferOutputs = True
config.General.transferLogs    = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'VBF_Htt_SMEFTsim_topU3l_quadratic_nanoaodsim_cfg.py'
config.JobType.allowUndistributedCMSSW = True
config.JobType.maxMemoryMB = 4000
config.JobType.maxJobRuntimeMin = 600
config.JobType.numCores = 8

config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 5
NJOBS = 50 # This is not a configuration parameter, but an auxiliary variable that we use in the next line.
config.Data.totalUnits = config.Data.unitsPerJob * NJOBS
config.Data.userInputFiles = [
    "root://cmseos.fnal.gov//store/group/lpchiggssbi/signal/VBFHtoTauTau/140X_mcRun3_2024_realistic_v26/miniaodsim_v2/0000/miniaodsim_{}.root".format(i) for i in range(1, config.Data.totalUnits + 1)
]
config.Data.publication = False
config.Data.outputPrimaryDataset = 'VBFHtoTauTau'
config.Data.outputDatasetTag     = '140X_mcRun3_2024_realistic_v26'

config.Site.whitelist = [
    'T2_US_Caltech',
    'T2_US_Florida',
    'T2_US_MIT',
    'T2_US_Nebraska',
    'T2_US_Purdue',
    'T2_US_UCSD',
    'T2_US_Vanderbilt',
    'T2_US_Wisconsin',
    'T1_US_FNAL',
    # "T2_CH_CERN"
]
config.Site.storageSite = 'T3_US_FNALLPC'
config.Data.outLFNDirBase = '/store/group/lpchiggssbi/signal'
