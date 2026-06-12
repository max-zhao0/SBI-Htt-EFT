from CRABClient.UserUtilities import config
config = config()

config.General.requestName     = 'VBF_Htt_SMEFTsim_topU3l_quadratic_SMpoint_gennanogen'
config.General.workArea        = 'crab_jobs'
config.General.transferOutputs = True
config.General.transferLogs    = True

config.JobType.pluginName = 'PrivateMC'
config.JobType.psetName = 'VBF_Htt_SMEFTsim_topU3l_quadratic_gennanogen_cfg.py'
config.JobType.allowUndistributedCMSSW = True
config.JobType.maxMemoryMB = 3000
config.JobType.maxJobRuntimeMin = 600
config.JobType.numCores = 1

config.Data.splitting = 'EventBased'
config.Data.unitsPerJob = 5000
NJOBS = 200 # This is not a configuration parameter, but an auxiliary variable that we use in the next line.
config.Data.totalUnits = config.Data.unitsPerJob * NJOBS
config.Data.publication = False
config.Data.outputPrimaryDataset = 'VBFHtoTauTau'
config.Data.outputDatasetTag     = '140X_mcRun3_2024_realistic_v26'

config.Site.storageSite = 'T3_US_FNALLPC'
config.Data.outLFNDirBase = '/store/group/lpchiggssbi/signal'
