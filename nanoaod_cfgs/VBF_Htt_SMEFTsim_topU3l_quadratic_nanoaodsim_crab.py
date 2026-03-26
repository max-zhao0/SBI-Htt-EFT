from CRABClient.UserUtilities import config
config = config()

config.General.requestName     = 'VBF_Htt_SMEFTsim_topU3l_quadratic_np0_nanoaodsim'
config.General.workArea        = 'crab_jobs'
config.General.transferOutputs = True
config.General.transferLogs    = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'VBF_Htt_SMEFTsim_topU3l_quadratic_nanoaodsim_cfg.py'
config.JobType.allowUndistributedCMSSW = True
config.JobType.maxMemoryMB = 4000
config.JobType.maxJobRuntimeMin = 60
config.JobType.numCores = 8

config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
NJOBS = 5 # This is not a configuration parameter, but an auxiliary variable that we use in the next line.
config.Data.totalUnits = config.Data.unitsPerJob * NJOBS
config.Data.userInputFiles = [
    "root://eosuser.cern.ch//eos/user/z/zhaom/qqHtoTauTau/140X_mcRun3_2024_realistic_v26/miniaodsim_np0/0000/miniaodsim_{}.root".format(i) for i in range(1, config.Data.totalUnits + 1)
]
config.Data.publication = False
config.Data.outputPrimaryDataset = 'qqHtoTauTau'
config.Data.outputDatasetTag     = '140X_mcRun3_2024_realistic_v26'

config.Site.whitelist = ['T2_CH_CERN']
config.Site.storageSite = 'T3_CH_CERNBOX'
