# manager

This is a GitHub organization managerial tool.  
The manager can be used to automate team formation, base code distribution, and submission collection.  
See the [wiki](https://github.com/GitHubClassroomTestCMPUT229/manager/wiki) for more details.  

## Setup

* Clone this repo.
* Navigate to the directory that contains the manager.
* Run setup.sh.
    * Initializes a Python virtual environment in the folder /venv/
    * Activates the virtual environment with "source venv/bin/activate"
    * Uses pip to install the dependencies PyGithub and GitPython
    * Deactivates the virtual environment with "deactivate"
* Obtain a GitHub Oauth token for the organization you are managing.
    * [How to obtain a GitHub Oauth token](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/)
    * Copy the token and write it to git.token in the manager's directory.
    * .gitignore prevents this file from being added to your repo, in case you are adding to this work.
* Setup is complete

## Run

* Navigate to the directory that contains the manager.
* Activate the virutal environment with the command "source venv/bin/activate"
* Run the manager with the command "classroom_manager.py [flags]"

## Flags

* -o \<organziation>: set [o]rganization name
* -r \<repo>: set [r]epo name
* -t: set [t]eams locally
* -s: [s]et repos for each team
* -g: [g]et repos from each team
* -x: clear local repos from specified repo
* -X: clear teams & repos on GitHub  

## Examples
* classroom_manager.py -o GitHubClassroomTestCMPUT229 -r testlab1 -t -s  
  * Tells the manager to set teams on GitHubClassroomTestCMPUT229, then distribute the base code located in GitHubClassroomTestCMPUT229/testlab1/ to each team.  
