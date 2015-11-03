from modules.Repos import Repos, getRepoCommits
from modules.Config import Config
from modules.GoSymbolsExtractor import GoSymbolsExtractor
from modules.ImportPathsDecomposer import ImportPathsDecomposer
from modules.ImportPath import ImportPath
import datetime
import json

# get imported packages from GoSymbolsExtractor
# decompose packages into classes
# for each class read all commits from upstream repository
# for each list of commits find the closest possible commit to inserted commit (based on date)

if __name__ == "__main__":
	r_obj = Repos()
	repos = r_obj.parseReposInfo()
	local_repos = {}
	upstream_repo = {}

	for name in repos:
		dir, repo = repos[name]

		m_repo = str.replace(repo, 'https://', '')
		m_repo = str.replace(m_repo, 'http://', '')
		if m_repo.endswith('.git'):
			m_repo = m_repo[:-4]
		if m_repo.endswith('.hg'):
			m_repo = m_repo[:-3]

		local_repos[m_repo] = dir
		upstream_repo[m_repo] = repo
	#print local_repos

	# 'golang-github-boltdb-bolt': ('/var/lib/gofed/packages/golang-github-boltdb-bolt/upstream//bolt', 'https://github.com/boltdb/bolt.git')
	# print repos

	path = "."
	commit_date = int(datetime.datetime.strptime('29/09/2015', '%d/%m/%Y').strftime("%s"))
	pull = True
	noGodeps = Config().getSkippedDirectories()
	importpath = "github.com/influxdb/influxdb"

	gse_obj = GoSymbolsExtractor(path, imports_only=True, skip_errors=True, noGodeps=noGodeps)
	if not gse_obj.extract():
		fmt_obj.printError(gse_obj.getError())
		exit(1)

	package_imports_occurence = gse_obj.getPackageImportsOccurences()

	ip_used = gse_obj.getImportedPackages()
	ipd = ImportPathsDecomposer(ip_used)
	if not ipd.decompose():
		fmt_obj.printError(ipd.getError())
		exit(1)

	warn = ipd.getWarning()
	if warn != "":
		fmt_obj.printWarning("Warning: %s" % warn)

	classes = ipd.getClasses()
	sorted_classes = sorted(classes.keys())

	json_file = {}
	json_file["ImportPath"] = importpath

	json_deps = []
	for element in sorted_classes:
		if element == "Native":
			continue

		# class name starts with prefix => filter out
		if importpath != "" and element.startswith(importpath):
			continue

		# convert each import path prefix to provider prefix
		ip_obj = ImportPath(element)
		if not ip_obj.parse():
			print ip_obj.getError()
			continue

		provider_prefix = ip_obj.getProviderPrefix()
		if provider_prefix not in local_repos:
			print "%s:" % provider_prefix
			continue

		#print local_repos[provider_prefix]
		path = local_repos[provider_prefix]
		upstream = upstream_repo[provider_prefix]

		commits = getRepoCommits(path, upstream, pull=pull)
		last_commit_date = 1
		last_commit = -1
		for commit in commits:
			if last_commit_date <= commits[commit]:
				last_commit_date = commits[commit]
				last_commit = commit
			else:
				break

		str_date = datetime.datetime.fromtimestamp(int(last_commit_date)).strftime('%Y-%m-%d %H:%M:%S')

		for ip in classes[element]:
			line = {}
			line["ImportPath"] = str(ip)
			line["Comment"] = str_date
			line["Rev"] = last_commit
			json_deps.append(line)
		#print "%s: %s" % (str(element), last_commit)

	json_file["Deps"] = json_deps

	print json.dumps(json_file, indent=4, sort_keys=False)

