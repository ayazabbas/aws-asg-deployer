# aws-asg-deployer
Python package + CLI tool to manage deploying new instances into AWS Autoscaling Groups.

```
Usage: asgd [OPTIONS] COMMAND [ARGS]...

  AWS ASG Deployer

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  deploy  Updates Autoscaling Group to use new AMI if provided and then performs an instance refresh.
```
