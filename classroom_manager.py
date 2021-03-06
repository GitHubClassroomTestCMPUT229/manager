#!/usr/bin/env python

import json
import shutil
from github import Github
from git import Repo
import time
import sys
import os

# REFERENCE
#----------------------------------------------------------------------------------------------
# Oauth tokens in gitpython    
# http://stackoverflow.com/questions/36358808/cloning-a-private-repo-using-https-with-gitpython
# User: shawnzhu
#
# Organizations & Membership
# https://github.com/PyGithub/PyGithub/issues/507
# User: lbrownell-gpsw
#----------------------------------------------------------------------------------------------

class Manager():
    def __init__(self, name):
        self.name = name
        self.url = "https://github.com/{}/".format(name)
        token = self.get_token()
        self.hub = Github(token)        
        self.org = self.hub.get_organization(name)

    # Purpose:
    #   Reads git.token to get the oauth token that allows PyGithub and GitPython 
    #   to perform their actions.
    def get_token(self):
        f = open("git.token", "r")
        token = f.readline().strip()
        return token

    # Params:
    #   hub: PyGitHub github object
    #   name: the name of the organization being retrieved
    # Purpose:
    #   Get access to the PyGitHub abstraction of the classroom
    # Returns:
    #   An instance of PyGitHub abstraction of the GitHub service
    def get_org(self):
        print self.hub
        return self.hub.get_organization(self.name)

    # Params:
    #   hub: PyGitHub github object
    #   org: PyGitHub organization object
    # Purpose:
    #   To iterate over all the GitHub IDs in a class.txt file
    #   and add the GitHub users to the organization's membership.
    # N.B.: class.txt is a text file with student gitIDs on each line
    def set_members(self):
        class_list = open("./class/class.txt", "r")
        c = [line.strip() for line in c]
        class_list.close()

        for student in c:
            self.org.add_to_public_members(self.hub.get_user(student))

    # Default: Each student in the class is in their own team
    # Nondefault:   If students are allowed to form groups, then their groups should
    #               be identified in teams.txt
    # Should check that students are not member of more than one group.
    # class.txt is a text file with student gitIDs on each line
    # teams.txt is a text file that identifies which student gitIDs are proposed
    # to be group members.  Groups are separated by the term "team:".
    # team:
    # <member>
    # <member>
    # team:
    # <member>
    @staticmethod
    def set_teams():
        print "Parsing class & team files."
        teams = {}
        class_list = open("./class/class.txt", "r")
        teams_list = open("./class/teams.txt", "r")
        t = teams_list.readlines()
        c = class_list.readlines()
        t = [line.strip() for line in t]
        c = [line.strip() for line in c]
        i = 0
        class_list.close()
        teams_list.close()

        for line in c:
            line = line.strip()
            if line in t:
                pass    # Skip over students in groups
            else:
                team_name = "team" + str(i)
                teams[team_name] = [line]
                i += 1
        for j in range(len(t)):
            team_name = "team" + str(i)
            team = []
            if t[j] == "team:":
                j += 1
                while t[j] != "team:":
                    if t[j] != "":
                        team.append(t[j])
                    j += 1
                    if j == len(t):
                        break
                teams[team_name] = team
                i += 1

        out = open("./class/team_defs.json", "w")
        json.dump(teams, out)
        out.close()

    # Purpose:
    #   Write the team defs as csv
    #   Format: <team>,<member>\n
    def json_to_csv(self):
        f = open("./class/team_defs.json", "r")
        teams = json.load(f)
        f.close()

        out = open("./class/team_defs.csv", "w")
        for team in teams:
            for member in teams[team]:
                out.write("{},{}\n".format(team,member))
        out.close()

    # Purpose:
    #   Write the team defs as csv
    #   Format: <team>,<member>\n
    def git_to_csv(self):
        out = open("./class/team_defs.csv", "w")
        teams = self.get_git_teams()
        for team in teams:
            members = [m for m in team.get_members()]
            for member in members:
                out.write("{},{}\n".format(team.name,member.login))
        out.close()

    # Params:
    #   hub: PyGitHub github object
    #   org: PyGitHub organization object
    # Purpose:
    #   To iterate over all the teams defined locally with ten_defs.json
    #   and create teams on GitHub.
    def set_git_teams(self):
        print "Setting teams on GitHub."

        f = open("./class/team_defs.json", "r")
        teams = json.load(f)
        f.close()

        for team in teams.keys():
            t = None
            try:
                t = self.org.create_team(team)
                print "Created " + team + " on GitHub."
            except:
                print "Error creating team: team {} already exists.".format(team)
            for member in teams[team]:
                t.add_to_members(self.hub.get_user(member))
    
    # Purpose:
    #   Gets the PyGitHub teams
    def get_git_teams(self):
        results = [team for team in self.org.get_teams()]
        return results

    # Param:
    #   team: name of a team on GitHub
    #   member: name of a member of the organization
    # Purpose:
    #   Add member to team
    def add_members(self, team, members):
        teams = {t.name: t.id for t in self.org.get_teams()}
        team = self.org.get_team(teams[team])
        for member in members:
            team.add_to_members(self.hub.get_user(member))

    # Param:
    #   team: name of a team on GitHub
    #   member: name of a member of the organization
    # Purpose:
    #   Remove member from team
    def del_members(self, team, members):
        teams = {t.name: t.id for t in self.org.get_teams()}
        team = self.org.get_team(teams[team])
        for member in members:
            team.remove_from_members(self.hub.get_user(member))

    # Param:
    #   org: PyGitHub organization object
    #   lab: string identifier for the base code for a lab.  Defaults to testlab1.
    # Purpose:
    #   To iterate over all the teams for the CMPUT229 GitHub organization and
    #   assign each team a clone of the repo containing the base code.
    def set_repos(self, lab="testlab1"):
        print "Setting repos for {}.".format(lab)
        teams = self.org.get_teams()

        repos = {}
        try:
            print "Setting local clone of base code."
            base, url = self.local_clone(lab)
            repos["instructor"] = {lab: url}
        except Exception as e:
            print "Error making local clone of base code."
            print e
            return

        for team in teams:
            if team.name != "Students":
                try:
                    print "Assigning " + team.name + " the repo."
                    team_repo = self.clone(lab, team, base) 
                    repos[team.name] = team_repo
                except Exception as e:
                    print "Error cloning lab for " + team.name
                    print e
                    time.sleep(5)
                    print "Waiting before trying again."
                    try:
                        print "Assigning " + team.name + " the repo."
                        team_repo = self.clone(lab, team, base) 
                        repos[team.name] = team_repo
                    except Exception as e:
                        print "Error cloning lab for " + team.name
                        print e

    # Param:
    #   lab: String
    # Purpose:
    #   Gather all repos from all teams matching the lab
    #   Used to collect assignments
    #   Used to get local copies to submit to moss
    def get_repos(self, lab):
        print "Getting repos from GitHub."
        teams = self.get_git_teams()
        teams = [team.name for team in teams]
        teams.remove("Students")
        for team in teams:
            url = "{}{}".format(self.url, "{}_{}".format(team, lab))
            clone_path = "./{}/{}/".format(lab, team)
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            Repo.clone_from(self.insert_auth(url), clone_path)

        base_url = "{}{}".format(self.url, lab)
        base_path = "./{}/instructor/".format(lab)
        if os.path.exists(base_path):
            shutil.rmtree(base_path)
        Repo.clone_from(self.insert_auth(base_url), base_path)

    # Param:
    #   lab: String lab
    # Purpose:
    #   to iterate over all students by team in order to notify them
    #   that the lab has been assigned.
    def notify_all(self, lab):
        for team in self.org.get_teams():
            if team.name != "Students":
                for member in team.get_members():
                    self.notify(member, team, lab)

    # Param:
    #   member: PyGitHub member
    #   team:   PyGitHub team
    #   lab:    String
    # Purpose:
    #   Send an email to each member of a team to notify them that their
    #   repo has been assigned.
    def notify(self, member, team, lab):
        # TODO: Send an email to the github email.
        pass
    # Param:
    #   Lab: Which lab/assignment will be deleted
    # Purpose:
    #   Deletes local files for lab
    def del_local_repos(self, lab="testlab1"):
        clone_path = "./{}/".format(lab)
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)

    # Param:
    #   org: PyGitHub organization object
    #   lab: string identifier for a lab.  Defaults to testlab1.
    # Purpose:
    #   Iterates over all repos for all teams in the organization and 
    #   deletes each team's repo for a given lab.
    def del_git_repos(self):
        teams = self.org.get_teams()
        for team in teams:
            repos = team.get_repos()
            for repo in repos:
                print "Deleting repo " + repo.name
                repo.delete()

    # Param:
    #   org: PyGitHub organization object
    # Iterates over all teams in the organization & deletes them.
    def del_git_teams(self):
        teams = self.org.get_teams()
        for team in teams:
            if team.name != "Students":
                members = team.get_members()
                for member in members:
                    team.remove_from_members(member)
                print "Deleting team " + team.name
                team.delete()

    # Params:
    #   lab: identifier for the lab, eg "lab1".
    #   team: PyGitHub team object.
    #   base_repo: GitPython repo object.
    #   org: PyGitHub organization object
    # Purpose:
    #   Distributes the repo to a team from a local copy of the repo.
    # Returns:
    #   A dictionary mapping the lab identifier to the url of the team's clone.
    def clone(self, lab, team, base_repo):
        base_url = self.url+lab
        repo_name = "{}_{}".format(team.name, lab)
        repo_url = self.url + repo_name
        team_repo = self.org.create_repo(repo_name, team_id=team)
        remote = base_repo.create_remote(team_repo.name, self.insert_auth(repo_url))
        remote.push()  
        return {lab: repo_url}

    # Param:
    #   lab: string identifier for a lab
    # Purpose:
    #   Creates a local copy of the lab's base code in order to distribute it to students in the class.
    # Return:
    #   GitPython Repo object
    def local_clone(self, lab):
        token = self.get_token()
        url = self.url+lab
        if os.path.exists("./base/"):
            shutil.rmtree("./base/")
        base_repo = Repo.clone_from(self.insert_auth(url), "./base/")
        return base_repo, url

    # Removes the local copy of the repo after distribution 
    def remove_local(self):
        shutil.rmtree("./base/")

    # Param:
    #   url: string representation of a GitHub resource.
    # Purpose:
    #   Inserts an oauth token in the url to make access easier, and to keep from committing 
    #   oauth tokens to git repos.  It lets the url remain unaltered at the higher scope.
    #   Needed for access using GitPython (different interface from PyGitHub).
    # Returns:
    #   The url, but with oauth token inserted
    def insert_auth(self, url):
        token = self.get_token()
        url = url[:url.find("://")+3] + token + ":x-oauth-basic@" + url[url.find("github"):]
        return url
    
    # https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    def get_commits(self, team, lab):
        name = "{}_{}".format(team, lab)
        repo = self.org.get_repo(name)
        commits = [c for c in repo.get_commits()]
        commits.sort(key=lambda c: time.strptime(str(c.commit.author.date), "%Y-%m-%d %H:%M:%S"))
        return commits

    def get_deadline(self, lab):
        deadlines_file = open("./class/deadlines.csv", "r")
        d = deadlines_file.readlines()
        deadlines_file.close()

        deadlines = {}
        for line in d:
            l, date = line.split(",")
            deadlines[l] = date.strip()
        return time.strptime(deadlines[lab], "%Y-%m-%d %H:%M:%S")

    def get_repo_by_deadline(self, team, lab):
        deadline = self.get_deadline(lab)
        commits = self.get_commits(team, lab)
        commit = commits[0]

        for c in commits[1:]:
            date = time.strptime(str(c.commit.author.date), "%Y-%m-%d %H:%M:%S")
            if date <= deadline:
                commit = c
            else:
                break

        return commit

# Purpose:
#   Returns a dictionary used to represent default values for the manager to use.
def defaults():
    try:
        f = open("./class/defaults.json", "r")
        defaults = json.load(f)
        f.close()   
        return defaults
    except:
        return None

# Param:
#   field: field in defaults.json to be update.
#   new_value: the value to overwrite where the field is.
# Purpose:
#   Updates the default values used for the manager to the most-recently used ones.
def update(field, new_value):
    try:
        f = open("./class/defaults.json", "r")
        defaults = json.load(f)
        f.close()
        defaults[field] = new_value
        f = open("./class/defaults.json", "w")
        json.dump(defaults, f)
        return
    except:
        return



# flags:    
'''
-o <organization_name>: set organization name           ([o]rg set)
-r <repo_name>: set repo for script                     ([r]epo set)
-t: set teams for the organization locally              ([t]eams set)
-a <team_name> <member>: Add <member> to <team>         ([a]dd member)
-d <team_name> <member>: delete <member> from <team>    ([d]emove member)
-s: distribute base repo (-r <repo>) to teams on GitHub ([s]et repos)
-n: notify students of repo distribution                ([n]otify)
-g: collect repos (-r <base_repo>) from students        ([g]et repos)
-x: clear local repos (-r <assignment>)
-X: clear teams & repos on GitHub
'''

def main():
    org_name = ""
    repo_name = ""
    args = sys.argv

    if "-h" in args:
        print """--------------------------------------------------------------------
This is a list of flags on the command-line:

-o <organization_name>: set organization name           ([o]rg set)
-r <repo_name>: set repo for script                     ([r]epo set)
-t: set teams for the organization locally              ([t]eams set)
-a <team_name> <member>: Add <member> to <team>         ([a]dd member)
-d <team_name> <member>: delete <member> from <team>    ([d]emove member)
-s: distribute base repo (-r <repo>) to teams on GitHub ([s]et repos)
-n: notify students of repo distribution                ([n]otify)
-g: collect repos (-r <base_repo>) from students        ([g]et repos)
-x: clear local repos (-r <assignment>)
-X: clear teams & repos on GitHub
--------------------------------------------------------------------
"""

    if "-o" in args:
        i = args.index("-o")+1
        org_name = args[i]
        i += 1
        while i < len(args) and args[i][0] != "-":
            org_name += " {}".format(args[i])     # Set org name
            i += 1
        update("org", org_name)
    else:
        if defaults():
            org_name = defaults()["org"]
        else:
            return 1

    m = Manager(org_name)

    if "-t" in args:
        m.set_teams()                           # local
        m.set_git_teams()                       # remote
        m.git_to_csv()                          # setup csv for teams

    if "-a" in args:
        team = args[args.index("-a")+1]
        start = args.index("-a")+2
        end = start
        while end < len(args):
            if args[end][0] == "-":
                break
            end += 1
        members = args[start:end]               # set members
        args = args[:start-2] + args[end:]
        m.add_members(team, members)

    if "-d" in args:
        team = args[args.index("-d")+1]
        start = args.index("-d")+2
        end = start
        while end < len(args):
            if args[end][0] == "-":
                break
            end += 1
        members = args[start:end]
        args = args[:start-2] + args[end:]      # set members
        m.del_members(team, members)

    if "-r" in args:
        repo_name = args[args.index("-r")+1]    # Set lab name
        update("repo", repo_name)
    else:
        if defaults():
            repo_name = defaults()["repo"]
        else:
            return 1
    
    m.get_commits("team0", "lab0.0")
    m.get_deadline("lab0.0")
    print m.get_repo_by_deadline("team0", "lab0.0").commit.author.date
    return

    if "-s" in args:
        m.set_repos(repo_name)                  # Set github repos
    
    if "-n" in args:
        m.notify_all(repo_name)

    if "-g" in args:
        m.get_repos(repo_name)                  # get github repos

    if "-x" in args:
        print "THIS WILL CLEAR THE LOCAL REPOS FOR {}.".format(repo_name)
        confirm = (raw_input("Are you sure? [y/n]: ")[0].lower() == 'y')
        if confirm:
            m.del_local_repos(repo_name)        # remove local repos

    if "-X" in args:
        print "THIS WILL CLEAR ALL TEAM REPOS & TEAMS FROM GitHub."
        confirm = (raw_input("Are you sure? [y/n]: ")[0].lower() == 'y')
        if confirm:
            m.del_git_repos()                   # remove remote repos
            m.del_git_teams()                   # remove remote teams
    return

if __name__ == "__main__":
    main()

