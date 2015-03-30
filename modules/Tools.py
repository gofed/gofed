from Utils import runCommand
from Config import Config
import os
import threading
import subprocess

BUILDURL="http://koji.fedoraproject.org/koji/taskinfo?taskID=%s"

# DRY MODE
# - don't run any command changing a state
#
# DECOMPOSITION
# - low level commands
# - simple commands (wrappers over low level commands)
# - multi commands (running simple commands over chosen branches)

class LowLevelCommand:

	def __init__(self, dry=False, debug=False):
		self.dry = dry
		self.debug = debug

	def runFedpkgSrpm(self):
		"""
		Run 'fedpkg srpm'.
		It returns so, se, rc triple.
		"""
		if self.debug == True:
			print "Running 'fedpkg srpm'"

		if self.dry == True:
			so = "Wrote: gofed-test-0.6.2-0.3.git89088df.fc20.src.rpm"
			se = ""
			rc = 0
			return so, se, rc
		else:
			return runCommand("fedpkg srpm")

	def runFedpkgScratchBuild(self, srpm):
		"""
		Run 'fedpkg scratch-build --nowait --srpm=SRPM'
		"""
		if self.debug == True:
			print "Running 'fedpkg scratch-build --nowait --srpm=SRPM'"

		if self.dry == True:
			so = "Created task: 1"
			se = ""
			rc = 0
			return so, se, rc
		else:
			return runCommand("fedpkg scratch-build --nowait --srpm=%s" % srpm)

	def runFedpkgBuild(self):
		"""
		Run 'fedpkg build --nowait'
		"""
		if self.debug == True:
			print "Running 'fedpkg build --nowait'"

		if self.dry == True:
			so = "Created task: 1"
			se = ""
			rc = 0
			return so, se, rc
		else:
			return runCommand("fedpkg build --nowait")

	def runGitPull(self):
		"""
		Run 'git pull'.
		It returns so, se, rc triple.
		"""
		if self.debug == True:
			print "Running 'git pull'"

		if self.dry == True:
			so = ""
			se = ""
			rc = 0
			return so, se, rc
		else:
			return runCommand("git pull")

	def runFedpkgPush(self):
		"""
		Run 'fedpkg push'.
		It returns so, se, rc triple.
		"""
		if self.debug == True:
			print "Running 'fedpkg push'"

		if self.dry == True:
			so = ""
			se = ""
			rc = 0
			return so, se, rc
		else:
			return runCommand("fedpkg push")

	def runFedpkgUpdate(self):
		"""
		Run 'fedpkg update'.
		It returns so, se, rc triple.
		"""
		if self.debug == True:
			print "Running 'fedpkg update'"

		if self.dry == True:
			so = ""
			se = ""
			rc = 0
			return so, se, rc
		else:
			subprocess.call("fedpkg update", shell=True)
			return ""

	def runFedpkgSwitchBranch(self, branch):
		"""
		Run 'fedpkg switch-branch'.
		It returns so, se, rc triple.
		"""
		if self.debug == True:
			print "Running 'fedpkg switch-branch'"

		if self.dry == True:
			so = ""
			se = ""
			rc = 0
			return so, se, rc
		else:
			return runCommand("fedpkg switch-branch %s" % branch)

	def runFedpkgCherryPick(self, branch):
		"""
		Run 'git cherry-pick BRANCH'.
		It returns so, se, rc triple.
		"""
		if self.debug == True:
			print "Running 'git cherry-pick BRANCH'"

		if self.dry == True:
			so = ""
			se = ""
			rc = 0
			return so, se, rc
		else:
			return runCommand("git cherry-pick %s" % branch)

	def runGitReset(self, branch):
		"""
		Run 'git reset --hard remotes/origin/BRANCH'.
		It returns so, se, rc triple.
		"""
		if self.debug == True:
			print "Running 'git reset --hard remotes/origin/%s'" % branch

		if self.dry == True:
			so = ""
			se = ""
			rc = 0
			return so, se, rc
		else:
			return runCommand("git reset --hard remotes/origin/%s" % branch)

class SimpleCommand:

	def __init__(self, dry=False, debug=False):
		self.dry = dry
		self.debug = debug
		self.llc = LowLevelCommand(dry=self.dry, debug=self.debug)

	def makeSRPM(self):	
		so, _, rc = self.llc.runFedpkgSrpm()
		if rc != 0:
			return ""

		for line in so.split("\n"):
			line = line.strip()
			if line == "":
				continue

			parts = line.split(" ")
			if len(parts) != 2:
				continue

			return parts[1]

		return ""

	def runBuild(self):
		so, _, rc = self.llc.runFedpkgBuild()
		if rc != 0:
			return -1

		task_lines = filter(lambda l: l.startswith("Created task:"), so.split("\n"))
		if len(task_lines) != 1:
			return -1

		task_id = task_lines[0].strip().split(" ")[-1]
		if task_id.isdigit():
			return int(task_id)

		return -1

	def runScratchBuild(self, srpm):
		so, _, rc = self.llc.runFedpkgScratchBuild(srpm)
		if rc != 0:
			return -1

		task_lines = filter(lambda l: l.startswith("Created task:"), so.split("\n"))
		if len(task_lines) != 1:
			return -1

		task_id = task_lines[0].strip().split(" ")[-1]
		if task_id.isdigit():
			return int(task_id)

		return -1

	def pullBranch(self, branch):
		so, se, rc = self.llc.runGitPull()
		if rc != 0:
			return se

		return ""

	def pushBranch(self, branch):
		so, se, rc = self.llc.runFedpkgPush()
		if rc != 0:
			return se

		return ""

	def updateBranch(self, branch):
		self.llc.runFedpkgUpdate()

		return ""

class WatchTaskThread(threading.Thread):
	def __init__(self, task_id):
		super(WatchTaskThread, self).__init__()
		self.task_id = task_id
		self.err = ""

	def run(self):
		runCommand("koji watch-task %s --quiet" % self.task_id)

	def getError(self):
		return self.err

class WaitTaskThread(threading.Thread):
	def __init__(self, task_id):
		super(WaitTaskThread, self).__init__()
		self.task_id = task_id
		self.state = False
		self.err = ""

	def run(self):
		so, se, rc = runCommand("koji taskinfo %s" % self.task_id)
		if rc != 0:
			self.err = "Unable to get taskinfo for %s branch's %s task: %s" % (branch, task_id, se)
			return

		state_lines = filter(lambda l: l.startswith("State"), so.split("\n"))

		state = state_lines[0].split(" ")[1]
		if state == "closed":
			self.state = True

	def getState(self):
		return self.state

	def getError(self):
		return self.err

class MultiCommand:

	def __init__(self, dry=False, debug=False):
		self.dry = dry
		self.debug = debug
		self.sc = SimpleCommand(debug=self.debug, dry=self.dry)
		self.llc = LowLevelCommand(debug=self.debug, dry=self.dry)

	def _buildBranches(self, branches, scratch=True):

		task_ids = {}
		# init [scratch] builds
		for branch in branches:
			print "Branch %s" % branch

			so, _, rc = self.llc.runFedpkgSwitchBranch(branch)
			if rc != 0:
				print "Unable to switch to %s branch" % branch
				continue

			srpm = ""
			if scratch:
				srpm = self.sc.makeSRPM()
				if srpm == "":
					print "Unable to create srpm"
					continue

			task_id = -1
			if scratch:
				task_id = self.sc.runScratchBuild(srpm)
			else:
				task_id = self.sc.runBuild()

			if task_id == -1:
				print "Unable to initiate task"
				continue

			task_ids[branch] = task_id
		
			if scratch:
				print "Scratch build %s initiated" % (BUILDURL % task_id)
			else:
				print "Build %s initiated" % (BUILDURL % task_id)

		return task_ids

	def _waitForTasks(self, task_ids):

		thread_list = {}
		for branch in task_ids:
			task_id = task_ids[branch]
			print "Watching %s branch, %s" % (branch, BUILDURL % task_id)
			if self.dry == False:
				thread_list[branch] = WatchTaskThread(task_id)
				thread_list[branch].start()

		if self.dry == False:
			for branch in task_ids:
				thread_list[branch].join()
				err = thread_list[branch].getError()
				if err != "":
					print err

	def _checkTasks(self, task_ids):
		all_done = True
		print "Checking finished tasks..."
		thread_list = {}

		if self.dry == False:
			for branch in task_ids:
				task_id = task_ids[branch]
				thread_list[branch] = WaitTaskThread(task_id)
				thread_list[branch].start()

			for branch in task_ids:
				thread_list[branch].join()

		for branch in task_ids:
			if self.dry == True:
				print "%s: closed" % branch
				continue

			if thread_list[branch].getState():
				print "%s: closed" % branch
			else:
				all_done = False
				print "%s: failed" % branch

		return all_done

	def scratchBuildBranches(self, branches):
		# init [scratch] builds
		task_ids = self._buildBranches(branches)
		print ""

		# wait for builds
		self._waitForTasks(task_ids)
		print ""

		# check out builds
		return self._checkTasks(task_ids)

	def buildBranches(self, branches):

		# init [scratch] builds
		task_ids = self._buildBranches(branches, scratch=False)
		print ""

		# wait for builds
		self._waitForTasks(task_ids)
		print ""

		# check out builds
		return self._checkTasks(task_ids)

	def pullBranches(self, branches):
		print "Pulling from branches: %s" % ", ".join(branches)

		all_done = True
		for branch in branches:
			print "Branch %s" % branch
			so, _, rc = self.llc.runFedpkgSwitchBranch(branch)
			if rc != 0:
				print "Unable to switch to %s branch" % branch
				all_done = False
				continue

			err = self.sc.pullBranch(branch)
			if err != "":
				print "%s: %s" % (branch, err)
				all_done = False

		return all_done

	def pushBranches(self, branches):
		print "Pushing to branches: %s" % ",".join(branches)

		all_done = True
		for branch in branches:
			print "Branch %s" % branch
			so, _, rc = self.llc.runFedpkgSwitchBranch(branch)
			if rc != 0:
				print "Unable to switch to %s branch" % branch
				all_done = False
				continue

			err = self.sc.pushBranch(branch)
			if err != "":
				print "%s: %s" % (branch, err)
				all_done = False

		return all_done

	def updateBranches(self, branches):
		print "Updating branches: %s" % ",".join(branches)

		all_done = True
		for branch in branches:
			print "Branch %s" % branch
			so, _, rc = self.llc.runFedpkgSwitchBranch(branch)
			if rc != 0:
				print "Unable to switch to %s branch" % branch
				all_done = False
				continue

			err = self.sc.updateBranch(branch)
			if err != "":
				print "%s: %s" % (branch, err)
				all_done = False

		return all_done

	def cherryPickMaster(self, branches, verbose=True):
		err = []
		for branch in branches:
			if branch == "master":
				continue

			_, _, rc = self.llc.runFedpkgSwitchBranch(branch)
			if rc != 0:
				err.append("Unable to switch to %s branch" % branch)
				err.append("Skipping %s branch" % branch)
				if verbose:
					print "\n".join(err)
				continue

			if verbose:
				print "Switched to %s branch" % branch

			_, se, rc = self.llc.runFedpkgCherryPick("master")
			if rc != 0:
				err.append("%s: unable to cherry pick master: %s" % (branch, se))
				if verbose:
					print err[-1]

		return err

	def resetBranchesToOrigin(self, branches):
		for branch in branches:
			_, _, rc = self.llc.runFedpkgSwitchBranch(branch)
			if rc != 0:
				print "Warning: unable to switch to %s branch" % branch
				print "Skipping %s branch" % branch
				continue

			print "Switched to %s branch" % branch
			so, se, rc = self.llc.runGitReset(branch)


STEP_CLONE_REPO=1
STEP_DOWNLOAD_SRPM=2
STEP_IMPORT_SRPM=3
STEP_HAS_RESOLVES=4
STEP_CLONE_TO_BRANCHES=5
STEP_SCRATCH_BUILD=6
STEP_PUSH=7
STEP_BUILD=8
STEP_UPDATE=9
STEP_OVERRIDE=10

STEP_END=10

class PhaseMethods:

	def __init__(self, dry=False, debug=False):
		self.phase = STEP_END
		self.mc = MultiCommand(dry=dry, debug=debug)
		self.branches = Config().getBranches()

	def setBranches(self, branches):
		self.branches = branches

	def startWithScratchBuild(self):
		self.phase = STEP_SCRATCH_BUILD

	def startWithPush(self):
		self.phase = STEP_PUSH

	def startWithBuild(self):
		self.phase = STEP_BUILD

	def startWithUpdate(self):
		self.phase = STEP_UPDATE

	def runPhase(self, phase):
		if phase == STEP_SCRATCH_BUILD:
			return self.mc.scratchBuildBranches(self.branches)

		if phase == STEP_PUSH:
			return self.mc.pushBranches(self.branches)

		if phase == STEP_BUILD:
			return self.mc.buildBranches(self.branches)

		if phase == STEP_UPDATE:
			branches = Config().getUpdates()
			branches = list(set(branches) & set(self.branches))
			return self.mc.updateBranches(branches)

		return 1

	def getPhaseName(self, phase):
		if phase == STEP_SCRATCH_BUILD:
			return "Scratch build phase"

		if phase == STEP_PUSH:
			return "Push phase"

		if phase == STEP_BUILD:
			return "Build phase"

		if phase == STEP_UPDATE:
			return "Update phase"

		return ""	

	def run(self):

		for i in range(1, STEP_END):
			if i < self.phase:
				continue

			phase_name = self.getPhaseName(i)
			if phase_name == "":
				print "Phase %s unknown" % i
				break

			print 60*"#"
			sl = len(phase_name)
			print ((60-sl)/2)*" " + phase_name
			print 60*"#"
			print ""

			if not self.runPhase(i):
				break	

