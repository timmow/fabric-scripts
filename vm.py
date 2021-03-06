from fabric.api import *

@task
def uptime():
    """Show uptime and load"""
    run('uptime')

@task
def free():
    """Show memory stats"""
    run('free')

@task
def disk():
    """Show disk usage"""
    run('df -kh')

@task
def os_version():
    """Show operating system"""
    run('facter lsbdistcodename lsbdistdescription operatingsystem operatingsystemrelease')

@task
def stopped_jobs():
    """Find stopped govuk application jobs"""
    with hide('running'):
        run('grep -l govuk_spinup /etc/init/*.conf | xargs -n1 basename | while read line; do sudo status "${line%%.conf}"; done | grep stop || :')

@task
def bodge_unicorn(name):
    """
    Manually kill off (and restart) unicorn processes by name

    e.g. To kill off and restart contentapi on backend-1 in Preview:

      fab preview -H backend-1.backend vm.bodge_unicorn:contentapi

    ...or on all backend hosts in Preview:

      fab preview class:backend vm.bodge_unicorn:contentapi

    Yes. This is a bodge. Sorry.
    """
    pid = run("ps auxwww | grep '/%s/' | grep -F 'unicorn master' | grep -v grep | awk '{ print $2 }' | xargs" % name)
    if pid:
        sudo("kill -9 %s" % pid)
    sudo("start '{0}' || restart '{0}'".format(name))

@task
def reload_unicorn(name):
    """
    Gracefully reloads a named Unicorn process.

    This is the same piped command we use when deploying applications.
    """
    sudo('sudo initctl start %s 2>/dev/null || sudo initctl reload %s' % (name, name))

@task
def reboot():
  """Schedule a host for downtime in nagios and reboot (if required)

  Usage:
  fab production -H frontend-1.frontend.production vm.reboot
  """
  from nagios import schedule_downtime
  result = run("/usr/local/bin/check_reboot_required 30 0", warn_only=True)
  if (not result.succeeded):      
      execute(schedule_downtime, env['host_string'])
      # we need to ensure we only execute this task on the current
      # host we're operating on, not every host in env.hosts
      execute(force_reboot, hosts=[env['host_string']])

@task
def force_reboot():
  """Schedule a host for downtime in nagios and force reboot (even if not required)"""
  run("sudo shutdown -r now")

@task
def poweroff():
  """Schedule a host for downtime in nagios and shutdown the VM

  Usage:
  fab production -H frontend-1.frontend.production vm.poweroff
  """
  from nagios import schedule_downtime
  execute(schedule_downtime, env['host_string'])
  run("sudo poweroff")
