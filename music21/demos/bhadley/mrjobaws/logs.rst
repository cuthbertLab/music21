All runs for extracting all features from bach 66.6
Experimenting with various instance types and time it takes to process.
Unfortunately no large differences found between single and multicore instances,
currently investigating if multicore processing is possible. As I currently
understanding it, Hadoop 0.20 is the latest available version that runs on Amazon EMR
and multicore processing is only available as of hadoop 0.21. booh. more investigation to come....

All output looked like this:

04846171e4361597962e3a3a6c29ca17|bach/bwv66.6.mxl|[[0.39655172413793105, 0.60344827586206895, 1.0, 0.17241379310344829, 0.13793103448275862, 0.13793103448275862, 0.034482758620689655, 0.15517241379310345, 0.051724137931034482, 0.0, 0.0, 0.0, 0.051724137931034482, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2.4402515723270439], [2], [1], [0.36477987421383645], [0.60344827586206906], [3], [0.33333333333333331], [0.14465408805031446], [0.22012578616352202], [0.58490566037735847], [0.11320754716981132], [0.056603773584905662], [0.012578616352201259], [0.018867924528301886], [0.47058823529411764], [10.285714285714286], [14.5], [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0.22085889570552147, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0.018082555402686495], [4], [1.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [12], [0.44171779141104295], [1.0], [0.25], [0.0], [0.34999999999999998], [0.15000000000000002], [0.4375], [0.17739268778674061], [120.0], [4, 4], [0], [0], [0], [0], [4], [3.9622641509433962], [0.19055669695022789], [0.1165644171779141], [0.19631901840490798], [0.94736842105263153], [0.90625], [5], [5], [3], [24], [10], [34], [0.4765625], [58.583333333333336], [0.18404907975460122], [0.76687116564417179], [0.049079754601226995], [1], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.052631578947368418, 0.0, 0.0, 0.052631578947368418, 0.052631578947368418, 0.26315789473684209, 0.0, 0.31578947368421051, 0.10526315789473684, 0.0, 0.052631578947368418, 0.15789473684210525, 0.52631578947368418, 0.0, 0.36842105263157893, 0.63157894736842102, 0.10526315789473684, 0.78947368421052633, 0.0, 1.0, 0.52631578947368418, 0.052631578947368418, 0.73684210526315785, 0.15789473684210525, 0.94736842105263153, 0.0, 0.36842105263157893, 0.47368421052631576, 0.0, 0.42105263157894735, 0.0, 0.36842105263157893, 0.0, 0.0, 0.052631578947368418, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.375, 0.03125, 0.5, 0.1875, 0.90625, 0.0, 0.4375, 0.6875, 0.09375, 0.875], [0.0, 0.0, 0.375, 0.6875, 0.5, 0.875, 0.90625, 1.0, 0.4375, 0.03125, 0.09375, 0.1875], [1]]|[[1], [1.2642604260880534], [3], [1.0], [0.60122699386503065], [1.5], [25], [12], [0.13207547169811321], [0.67924528301886788], [0.45283018867924529], [0.22641509433962265], [0.075471698113207544], [0.018867924528301886], [0.71698113207547165], [0.0], [0.02564102564102564], [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0], [0], [0]]	

==============
m2.2xlarge
===============

bhadley@ubuntu:~/Desktop$ python featureExtractionTest.py -r emr corpusPaths.txt > out15
/usr/lib/pymodules/python2.7/mpl_toolkits/__init__.py:2: UserWarning: Module _yaml was already imported from /usr/lib/python2.7/dist-packages/_yaml.so, but /usr/local/lib/python2.7/dist-packages is being added to sys.path
  __import__('pkg_resources').declare_namespace(__name__)
using configs in /home/bhadley/.mrjob.conf
using existing scratch bucket mrjob-caae57c3875e7ec1
using s3://mrjob-caae57c3875e7ec1/tmp/ as our scratch dir on S3
Uploading input to s3://mrjob-caae57c3875e7ec1/tmp/featureExtractionTest.bhadley.20120623.023304.931353/input/
creating tmp directory /tmp/featureExtractionTest.bhadley.20120623.023304.931353
writing master bootstrap script to /tmp/featureExtractionTest.bhadley.20120623.023304.931353/b.py
Copying non-input files into s3://mrjob-caae57c3875e7ec1/tmp/featureExtractionTest.bhadley.20120623.023304.931353/files/
Waiting 5.0s for S3 eventual consistency
Creating Elastic MapReduce job flow
Job flow created with ID: j-1SWUN6EPIE7CQ
Job launched 30.4s ago, status STARTING: Starting instances
Job launched 60.9s ago, status STARTING: Starting instances
Job launched 92.4s ago, status STARTING: Starting instances
Job launched 123.6s ago, status STARTING: Starting instances
Job launched 154.1s ago, status STARTING: Starting instances
Job launched 184.5s ago, status STARTING: Starting instances
Job launched 214.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 246.3s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 276.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 308.4s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 338.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 369.2s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 400.6s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 431.0s ago, status RUNNING: Running step
Job launched 462.5s ago, status RUNNING: Running step
Job launched 492.9s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.023304.931353: Step 1 of 1)
Opening ssh tunnel to Hadoop job tracker
Connect to job tracker at: http://localhost:40589/jobtracker.jsp
Job launched 524.4s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.023304.931353: Step 1 of 1)
 map 100% reduce   0%
Job completed.
Running time was 89.0s (not counting time spent waiting for the EC2 instances)
Fetching counters from S3...
Waiting 5.0s for S3 eventual consistency
Counters from step 1:
  (no counters found)
Streaming final output from s3://mrjob-caae57c3875e7ec1/tmp/featureExtractionTest.bhadley.20120623.023304.931353/output/
removing tmp directory /tmp/featureExtractionTest.bhadley.20120623.023304.931353
Removing all files in s3://mrjob-caae57c3875e7ec1/tmp/featureExtractionTest.bhadley.20120623.023304.931353/
Removing all files in s3://mrjob-caae57c3875e7ec1/tmp/logs/j-1SWUN6EPIE7CQ/
Killing our SSH tunnel (pid 6557)
Terminating job flow: j-1SWUN6EPIE7CQ

========================
c1.xlarge
=========================

bhadley@ubuntu:~/Desktop$ python featureExtractionTest.py -r emr corpusPaths.txt > out17
/usr/lib/pymodules/python2.7/mpl_toolkits/__init__.py:2: UserWarning: Module _yaml was already imported from /usr/lib/python2.7/dist-packages/_yaml.so, but /usr/local/lib/python2.7/dist-packages is being added to sys.path
  __import__('pkg_resources').declare_namespace(__name__)
using configs in /home/bhadley/.mrjob.conf
using existing scratch bucket mrjob-caae57c3875e7ec1
using s3://mrjob-caae57c3875e7ec1/tmp/ as our scratch dir on S3
Uploading input to s3://mrjob-caae57c3875e7ec1/tmp/featureExtractionTest.bhadley.20120623.025605.876127/input/
creating tmp directory /tmp/featureExtractionTest.bhadley.20120623.025605.876127
writing master bootstrap script to /tmp/featureExtractionTest.bhadley.20120623.025605.876127/b.py
Copying non-input files into s3://mrjob-caae57c3875e7ec1/tmp/featureExtractionTest.bhadley.20120623.025605.876127/files/
Waiting 5.0s for S3 eventual consistency
Creating Elastic MapReduce job flow
Job flow created with ID: j-2CUOGT3RYLT2F
Job launched 30.4s ago, status STARTING: Starting instances
Job launched 60.8s ago, status STARTING: Starting instances
Job launched 91.3s ago, status STARTING: Starting instances
Job launched 121.6s ago, status STARTING: Starting instances
Job launched 152.0s ago, status STARTING: Starting instances
Job launched 182.3s ago, status STARTING: Starting instances
Job launched 212.8s ago, status STARTING: Starting instances
Job launched 243.2s ago, status STARTING: Starting instances
Job launched 273.7s ago, status STARTING: Starting instances
Job launched 304.0s ago, status STARTING: Starting instances
Job launched 334.4s ago, status STARTING: Starting instances
Job launched 364.7s ago, status STARTING: Starting instances
Job launched 395.1s ago, status STARTING: Starting instances
Job launched 425.5s ago, status STARTING: Starting instances
Job launched 455.8s ago, status STARTING: Configuring cluster software
Job launched 486.2s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 516.6s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 546.9s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 577.3s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 607.7s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 638.0s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 668.4s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 698.7s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.025605.876127: Step 1 of 1)
Opening ssh tunnel to Hadoop job tracker
Connect to job tracker at: http://localhost:40495/jobtracker.jsp
Job launched 730.2s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.025605.876127: Step 1 of 1)
 map 100% reduce   0%
Job launched 760.8s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.025605.876127: Step 1 of 1)
 map 100% reduce   0%
Job launched 791.4s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.025605.876127: Step 1 of 1)
 map 100% reduce 100%
Job completed.
Running time was 108.0s (not counting time spent waiting for the EC2 instances)
Fetching counters from S3...
Waiting 5.0s for S3 eventual consistency
Counters from step 1:
  FileSystemCounters:
    S3_BYTES_READ: 29
    S3_BYTES_WRITTEN: 3986
  Job Counters :
    Launched map tasks: 3
    Rack-local map tasks: 3
  Map-Reduce Framework:
    Map input bytes: 17
    Map input records: 1
    Map output records: 1
    Spilled Records: 0
Streaming final output from s3://mrjob-caae57c3875e7ec1/tmp/featureExtractionTest.bhadley.20120623.025605.876127/output/
removing tmp directory /tmp/featureExtractionTest.bhadley.20120623.025605.876127
Removing all files in s3://mrjob-caae57c3875e7ec1/tmp/featureExtractionTest.bhadley.20120623.025605.876127/
Removing all files in s3://mrjob-caae57c3875e7ec1/tmp/logs/j-2CUOGT3RYLT2F/
Killing our SSH tunnel (pid 7098)
Terminating job flow: j-2CUOGT3RYLT2F

=========
m2.xlarge
==========

bhadley@ubuntu:~/Desktop$ python featureExtractionTest.py -r emr corpusPaths.txt > out18
/usr/lib/pymodules/python2.7/mpl_toolkits/__init__.py:2: UserWarning: Module _yaml was already imported from /usr/lib/python2.7/dist-packages/_yaml.so, but /usr/local/lib/python2.7/dist-packages is being added to sys.path
  __import__('pkg_resources').declare_namespace(__name__)
using configs in /home/bhadley/.mrjob.conf
using existing scratch bucket mrjob-b93cc3374c7945c2
using s3://mrjob-b93cc3374c7945c2/tmp/ as our scratch dir on S3
Uploading input to s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.032645.237283/input/
creating tmp directory /tmp/featureExtractionTest.bhadley.20120623.032645.237283
writing master bootstrap script to /tmp/featureExtractionTest.bhadley.20120623.032645.237283/b.py
Copying non-input files into s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.032645.237283/files/
Waiting 5.0s for S3 eventual consistency
Creating Elastic MapReduce job flow
Job flow created with ID: j-1NRHWKQJ2T0YH
Job launched 30.3s ago, status STARTING: Starting instances
Job launched 60.7s ago, status STARTING: Starting instances
Job launched 91.2s ago, status STARTING: Starting instances
Job launched 121.5s ago, status STARTING: Starting instances
Job launched 151.9s ago, status STARTING: Starting instances
Job launched 182.9s ago, status STARTING: Starting instances
Job launched 213.2s ago, status STARTING: Starting instances
Job launched 243.6s ago, status STARTING: Starting instances
Job launched 274.0s ago, status STARTING: Starting instances
Job launched 304.3s ago, status STARTING: Starting instances
Job launched 334.7s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 365.0s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 395.4s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 425.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 456.1s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 486.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 517.2s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 547.5s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 577.9s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.032645.237283: Step 1 of 1)
Opening ssh tunnel to Hadoop job tracker
Connect to job tracker at: http://localhost:40811/jobtracker.jsp
Job launched 609.3s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.032645.237283: Step 1 of 1)
 map 100% reduce   0%
Job launched 639.9s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.032645.237283: Step 1 of 1)
 map 100% reduce 100%
Job completed.
Running time was 88.0s (not counting time spent waiting for the EC2 instances)
Fetching counters from SSH...
Counters from step 1:
  FileSystemCounters:
    S3_BYTES_READ: 29
    S3_BYTES_WRITTEN: 3986
  Job Counters :
    Launched map tasks: 3
    Rack-local map tasks: 3
  Map-Reduce Framework:
    Map input bytes: 17
    Map input records: 1
    Map output records: 1
    Spilled Records: 0
Streaming final output from s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.032645.237283/output/
removing tmp directory /tmp/featureExtractionTest.bhadley.20120623.032645.237283
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.032645.237283/
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/logs/j-1NRHWKQJ2T0YH/
Killing our SSH tunnel (pid 7520)
Terminating job flow: j-1NRHWKQJ2T0YH

=============
m1.xlarge
=============

bhadley@ubuntu:~/Desktop$ python featureExtractionTest.py -r emr corpusPaths.txt > out19
/usr/lib/pymodules/python2.7/mpl_toolkits/__init__.py:2: UserWarning: Module _yaml was already imported from /usr/lib/python2.7/dist-packages/_yaml.so, but /usr/local/lib/python2.7/dist-packages is being added to sys.path
  __import__('pkg_resources').declare_namespace(__name__)
using configs in /home/bhadley/.mrjob.conf
using existing scratch bucket mrjob-b93cc3374c7945c2
using s3://mrjob-b93cc3374c7945c2/tmp/ as our scratch dir on S3
Uploading input to s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.034417.596298/input/
creating tmp directory /tmp/featureExtractionTest.bhadley.20120623.034417.596298
writing master bootstrap script to /tmp/featureExtractionTest.bhadley.20120623.034417.596298/b.py
Copying non-input files into s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.034417.596298/files/
Waiting 5.0s for S3 eventual consistency
Creating Elastic MapReduce job flow
Job flow created with ID: j-2KZ4FK72HCW7V
Job launched 30.4s ago, status STARTING: Starting instances
Job launched 61.8s ago, status STARTING: Starting instances
Job launched 92.1s ago, status STARTING: Starting instances
Job launched 122.5s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 152.9s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 183.3s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 213.6s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 244.0s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 274.5s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 304.9s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 335.3s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 365.6s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.034417.596298: Step 1 of 1)
Opening ssh tunnel to Hadoop job tracker
Connect to job tracker at: http://localhost:40436/jobtracker.jsp
Job launched 397.0s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.034417.596298: Step 1 of 1)
 map 100% reduce   0%
Job launched 427.6s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.034417.596298: Step 1 of 1)
 map 100% reduce   0%
Job completed.
Running time was 107.0s (not counting time spent waiting for the EC2 instances)
Fetching counters from S3...
Waiting 5.0s for S3 eventual consistency
Counters from step 1:
  FileSystemCounters:
    S3_BYTES_READ: 29
    S3_BYTES_WRITTEN: 3986
  Job Counters :
    Launched map tasks: 3
    Rack-local map tasks: 3
  Map-Reduce Framework:
    Map input bytes: 17
    Map input records: 1
    Map output records: 1
    Spilled Records: 0
Streaming final output from s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.034417.596298/output/
removing tmp directory /tmp/featureExtractionTest.bhadley.20120623.034417.596298
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.034417.596298/
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/logs/j-2KZ4FK72HCW7V/
Killing our SSH tunnel (pid 7642)
Terminating job flow: j-2KZ4FK72HCW7V

=======================
m1.large
=======================

bhadley@ubuntu:~/Desktop$ python featureExtractionTest.py -r emr corpusPaths.txt > out20
/usr/lib/pymodules/python2.7/mpl_toolkits/__init__.py:2: UserWarning: Module _yaml was already imported from /usr/lib/python2.7/dist-packages/_yaml.so, but /usr/local/lib/python2.7/dist-packages is being added to sys.path
  __import__('pkg_resources').declare_namespace(__name__)
using configs in /home/bhadley/.mrjob.conf
using existing scratch bucket mrjob-b93cc3374c7945c2
using s3://mrjob-b93cc3374c7945c2/tmp/ as our scratch dir on S3
Uploading input to s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.035956.544547/input/
creating tmp directory /tmp/featureExtractionTest.bhadley.20120623.035956.544547
writing master bootstrap script to /tmp/featureExtractionTest.bhadley.20120623.035956.544547/b.py
Copying non-input files into s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.035956.544547/files/
Waiting 5.0s for S3 eventual consistency
Creating Elastic MapReduce job flow
Job flow created with ID: j-2A4BY67L5OKXX
Job launched 30.3s ago, status STARTING: Starting instances
Job launched 60.7s ago, status STARTING: Starting instances
Job launched 91.0s ago, status STARTING: Starting instances
Job launched 121.5s ago, status STARTING: Starting instances
Job launched 151.8s ago, status STARTING: Starting instances
Job launched 182.2s ago, status STARTING: Configuring cluster software
Job launched 212.6s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 242.9s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 273.3s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 303.7s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 334.1s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 364.4s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 394.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 425.1s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 455.5s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.035956.544547: Step 1 of 1)
Opening ssh tunnel to Hadoop job tracker
Connect to job tracker at: http://localhost:40213/jobtracker.jsp
Job launched 487.9s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.035956.544547: Step 1 of 1)
 map 100% reduce   0%
Job launched 518.8s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.035956.544547: Step 1 of 1)
 map 100% reduce   0%
Job launched 550.2s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.035956.544547: Step 1 of 1)
 map 100% reduce   0%
Job launched 581.6s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.035956.544547: Step 1 of 1)
 map 100% reduce   0%
Job launched 612.4s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.035956.544547: Step 1 of 1)
 map 100% reduce 100%
Job completed.
Running time was 151.0s (not counting time spent waiting for the EC2 instances)
Fetching counters from S3...
Waiting 5.0s for S3 eventual consistency
Counters from step 1:
  FileSystemCounters:
    S3_BYTES_READ: 29
    S3_BYTES_WRITTEN: 3986
  Job Counters :
    Launched map tasks: 3
    Rack-local map tasks: 3
  Map-Reduce Framework:
    Map input bytes: 17
    Map input records: 1
    Map output records: 1
    Spilled Records: 0
Streaming final output from s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.035956.544547/output/
removing tmp directory /tmp/featureExtractionTest.bhadley.20120623.035956.544547
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.035956.544547/
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/logs/j-2A4BY67L5OKXX/
Killing our SSH tunnel (pid 7924)
Terminating job flow: j-2A4BY67L5OKXX

===========
m1.small
===========


bhadley@ubuntu:~/Desktop$ python featureExtractionTest.py -r emr corpusPaths.txt > out22
/usr/lib/pymodules/python2.7/mpl_toolkits/__init__.py:2: UserWarning: Module _yaml was already imported from /usr/lib/python2.7/dist-packages/_yaml.so, but /usr/local/lib/python2.7/dist-packages is being added to sys.path
  __import__('pkg_resources').declare_namespace(__name__)
using configs in /home/bhadley/.mrjob.conf
using existing scratch bucket mrjob-b93cc3374c7945c2
using s3://mrjob-b93cc3374c7945c2/tmp/ as our scratch dir on S3
Uploading input to s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.041727.532477/input/
creating tmp directory /tmp/featureExtractionTest.bhadley.20120623.041727.532477
writing master bootstrap script to /tmp/featureExtractionTest.bhadley.20120623.041727.532477/b.py
Copying non-input files into s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.041727.532477/files/
Waiting 5.0s for S3 eventual consistency
Creating Elastic MapReduce job flow
Job flow created with ID: j-1AUV23OW6JY6R
Job launched 30.3s ago, status STARTING: Starting instances
Job launched 60.8s ago, status STARTING: Starting instances
Job launched 91.1s ago, status STARTING: Starting instances
Job launched 121.4s ago, status STARTING: Starting instances
Job launched 151.8s ago, status STARTING: Configuring cluster software
Job launched 183.2s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 213.6s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 244.1s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 274.9s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 312.5s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 347.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 378.2s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 408.6s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 440.1s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 470.4s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 500.9s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 531.2s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 561.6s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 591.9s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 622.3s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
Opening ssh tunnel to Hadoop job tracker
Connect to job tracker at: http://localhost:40178/jobtracker.jsp
Job launched 653.7s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce   0%
Job launched 684.6s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce   0%
Job launched 715.4s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce   0%
Job launched 746.0s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce   0%
Job launched 776.7s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce   0%
Job launched 807.2s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce   0%
Job launched 837.8s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce   0%
Job launched 868.4s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce   0%
Job launched 899.0s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.041727.532477: Step 1 of 1)
 map 100% reduce 100%
Job completed.
Running time was 257.0s (not counting time spent waiting for the EC2 instances)
Fetching counters from S3...
Waiting 5.0s for S3 eventual consistency
Counters from step 1:
  FileSystemCounters:
    S3_BYTES_READ: 29
    S3_BYTES_WRITTEN: 3986
  Job Counters :
    Launched map tasks: 3
    Rack-local map tasks: 3
  Map-Reduce Framework:
    Map input bytes: 17
    Map input records: 1
    Map output records: 1
    Spilled Records: 0
Streaming final output from s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.041727.532477/output/
removing tmp directory /tmp/featureExtractionTest.bhadley.20120623.041727.532477
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.041727.532477/
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/logs/j-1AUV23OW6JY6R/
Killing our SSH tunnel (pid 8415)
Terminating job flow: j-1AUV23OW6JY6R


============
c1.medium
============

bhadley@ubuntu:~/Desktop$ python featureExtractionTest.py -r emr corpusPaths.txt > out23
/usr/lib/pymodules/python2.7/mpl_toolkits/__init__.py:2: UserWarning: Module _yaml was already imported from /usr/lib/python2.7/dist-packages/_yaml.so, but /usr/local/lib/python2.7/dist-packages is being added to sys.path
  __import__('pkg_resources').declare_namespace(__name__)
using configs in /home/bhadley/.mrjob.conf
using existing scratch bucket mrjob-b93cc3374c7945c2
using s3://mrjob-b93cc3374c7945c2/tmp/ as our scratch dir on S3
Uploading input to s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.043739.290840/input/
creating tmp directory /tmp/featureExtractionTest.bhadley.20120623.043739.290840
writing master bootstrap script to /tmp/featureExtractionTest.bhadley.20120623.043739.290840/b.py
Copying non-input files into s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.043739.290840/files/
Waiting 5.0s for S3 eventual consistency
Creating Elastic MapReduce job flow
Job flow created with ID: j-3BX1JRJCCV4H3
Job launched 30.3s ago, status STARTING: Starting instances
Job launched 60.7s ago, status STARTING: Starting instances
Job launched 91.1s ago, status STARTING: Starting instances
Job launched 122.5s ago, status STARTING: Starting instances
Job launched 153.9s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 184.2s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 214.5s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 244.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 275.1s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 305.4s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 335.8s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 366.1s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 396.4s ago, status BOOTSTRAPPING: Running bootstrap actions
Job launched 426.8s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.043739.290840: Step 1 of 1)
Opening ssh tunnel to Hadoop job tracker
Connect to job tracker at: http://localhost:40094/jobtracker.jsp
Job launched 458.2s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.043739.290840: Step 1 of 1)
 map 100% reduce   0%
Job launched 488.7s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.043739.290840: Step 1 of 1)
 map 100% reduce   0%
Job launched 519.2s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120623.043739.290840: Step 1 of 1)
 map 100% reduce 100%
Job completed.
Running time was 123.0s (not counting time spent waiting for the EC2 instances)
Fetching counters from S3...
Waiting 5.0s for S3 eventual consistency
Counters from step 1:
  FileSystemCounters:
    S3_BYTES_READ: 29
    S3_BYTES_WRITTEN: 3986
  Job Counters :
    Launched map tasks: 3
    Rack-local map tasks: 3
  Map-Reduce Framework:
    Map input bytes: 17
    Map input records: 1
    Map output records: 1
    Spilled Records: 0
Streaming final output from s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.043739.290840/output/
removing tmp directory /tmp/featureExtractionTest.bhadley.20120623.043739.290840
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/featureExtractionTest.bhadley.20120623.043739.290840/
Removing all files in s3://mrjob-b93cc3374c7945c2/tmp/logs/j-3BX1JRJCCV4H3/
Killing our SSH tunnel (pid 8534)
Terminating job flow: j-3BX1JRJCCV4H3


