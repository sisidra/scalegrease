Scalegrease
===========

A tool chain for scheduling, load balancing, deploying, running, and debugging data processing jobs.

DISCLAIMER
----------

**This is alpha software, occasionally not working.**  We are experimenting with creating
a project as open source from scratch.  Beware that this project may radically change in
incompatible ways until 1.0 is released, and that the development will be driven by Spotify's
internal needs for the near future.


Goals
=====

Provide a batch job execution platform, where data pipeline developers easily can express when and
how jobs should be run, without needing to operate dedicated machines for scheduling and execution.

Design goals:

* Stable under load.  Job execution service must not fall over under heavy
  load, e.g. when recomputing or backfilling.
* Minimal developer effort to package, deploy, schedule, and debug a batch
  job.
* Jobs run on a homogeneous cluster of tightly normalised machines, with
  few dependencies on software installed on the machines.  Jobs are
  self-contained.
* Integrate well with an efficient CI/CD workflow.
* Simplify failure debugging, without requiring users to locate which
  machine ran a particular job.
* Last but most importantly, separate the different scopes, describe below
  as much in order to be able to change implementation without affecting
  users heavily.
* No single point of failure.



Scopes
======

Running a batch computation involves multiple steps and considerations.  For the first iteration,
we will address the deployment, run, and debug scopes, described below.  For the other scopes, we
will use existing (Spotify) infrastructure, e.g. crontabs and Luigi, for the near future.
Regarding Luigi, it has a rich set of functionality, and parts of it will likely be used, at least
for the foreseeable future.


Dispatch
--------

A job can be dispatched in multiple ways:

* Manually.  A developer or analyst runs a one-off job.
* Scheduled.  Production jobs that run at regular intervals.
* Induced.  Production jobs that depend on input data sets, and run when
  the inputs are available.

Note that Luigi performs induced dispatch for multiple tasks packaged
together in a single module.  Such a sequence of tasks is regarded as a
single job from a scalegrease point of view.


Arbitration
-----------

Jobs need resources.  Resources should not be overallocated.  In times of
excessive load, drop jobs rather than overcommit resources.  

An arbiter typically keeps a queue of dispatched jobs, which are pulled or
pushed to workers capable of taking another job.


Deployment
----------

Getting the job implementation to the worker machine.  Avoid stateful
technologies, such as Debian packages and Puppet.



Execution
---------

Running the job, with the right runner script.

There will be cases for multiple types of runners:

* ShellRunner: Run a single shell script, shipped with the jar.
* HadoopRunner: Run with 'hadoop jar'.
* LuigiRunner: Unpack a Luigi job specification and use Luigi to execute it.


Debugging
---------

Collect the relevant execution tracing information, aka logs, to enable
debugging job failures.




Roadmap
=======

Iteration 1
-----------

Manual and scheduled dispatch are supported, via a simple sgdispatch
script.  Scheduled dispatch is supported in a primitive manner, with
crontab lines on redundant scheduling machines.

Arbitration through simple ZooKeeper-based queue, aka funnel, which
discards duplicate jobs.

Workers pull jobs from the funnel, and locally deploy a job jar, specified
in job description, from a central artifactory.

Logs are generated/copied to a common log directory, which should live on
shared storage, e.g. an NFS mount.


Iteration 2
-----------

Scheduled dispatch is specified in a schedule definition file in the job
source tree, with cron-like syntax.  A Jenkins job DSL file specifies that
the file should be pushed to a scheduling service as part of the CD chain.
A scheduling system dispatches it to the arbitration stage.  Possible
technologies:  Chronos, Azkaban, Aurora.

Depending on scheduling technology, it may also provide induced dispatch,
and sophisticated arbitration, e.g. with strong resource allocation and
isolation.  Possible technologies: Mesos, simpler ZK job queue without
deduplication.

