from CRABClient.UserUtilities import config
config = config()

config.General.requestName     = 'VBF_Htt_SMEFTsim_topU3l_quadratic_unpolarized_miniaodsim_200kevents'
config.General.workArea        = 'crab_jobs'
config.General.transferOutputs = True
config.General.transferLogs    = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'VBF_Htt_SMEFTsim_topU3l_quadratic_miniaodsim_cfg.py'
config.JobType.allowUndistributedCMSSW = True
config.JobType.maxMemoryMB = 3000
config.JobType.maxJobRuntimeMin = 240
config.JobType.numCores = 8

config.Data.userInputFiles = [
    "root://eosuser.cern.ch//eos/user/z/zhaom/qqHtoTauTau/140X_mcRun3_2024_realistic_v26/aodsim_v1/0000/aodsim_{}.root".format(i) for i in range(1, 11)
]
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 2
NJOBS = 5 # This is not a configuration parameter, but an auxiliary variable that we use in the next line.
config.Data.totalUnits = config.Data.unitsPerJob * NJOBS
config.Data.publication = False
config.Data.outputPrimaryDataset = 'qqHtoTauTau'
config.Data.outputDatasetTag     = '140X_mcRun3_2024_realistic_v26'

config.Site.whitelist = ['T2_CH_CERN']
config.Site.storageSite = 'T3_CH_CERNBOX'
