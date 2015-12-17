**Porting Music21 Processes to the Cloud**

This documentation and included code provides information about
running music21 processes through amazon web services. Running a program
on the cloud decreases runtime and is useful for large, computationally
intensive programs. When sending your task for computation on the cloud,
you can specify what type of EC2 instances and how many you'd like to use.
You only pay for what you use, and the cost of 1 hour of processing for a
decent EC2 instance is only about $0.165 per Hour.

Music21 jobs can easily be deployed to the amazon cluster using standard
map-reduce algorithms. The cluster, running a Hadoop framework, then
partitions the tasks among instances and returns data. mrjob, a python
module specifically designed to interface directly with Amazon Elastic MapReduce (EMR),
provides an abstracted and easy-to-use framework within which users may
write their processes. mrjob takes care of interfacing directly with Amazon EMR,
making it easy to run your music21 processes on the cloud with a simple
one-line command in the linux terminal.

**Map Reduce Algorithm**
Dean, J., Ghemawat,S.(2004).“MapReduce:Simplified data processing on large clusters,” 
Proceedings of the 6th Symposium on Operating System Design and Implementation, pp. 137–50.

From their paper:
"MapReduce is a programming model and an associated implementation for processing
and generating large datasets that is amenable to a broad variety of real-world tasks.
Users specify the computation in terms of a map and a reduce function, and the under-
lying runtime system automatically parallelizes the computation across large-scale clusters of
machines, handles machine failures, and schedules inter-machine communication to make 
efficient use of the network and disks. Programmers find the system easy to use: more than ten
thousand distinct MapReduce programs have been implemented internally at Google over the
past four years, and an average of one hundred thousand MapReduce jobs are executed on
Google’s clusters every day, processing a total of more than twenty petabytes of data per day."

**Amazon Elastic MapReduce**
`see full documentation here <http://aws.amazon.com/elasticmapreduce/>`_  

Excerpt from full documentation:

"Amazon Elastic MapReduce (Amazon EMR)
is a web service that enables businesses, researchers, data analysts, and 
developers to easily and cost-effectively process vast amounts of data. 
It utilizes a hosted Hadoop framework running on the web-scale infrastructure 
of Amazon Elastic Compute Cloud (Amazon EC2) and Amazon Simple Storage Service (Amazon S3).

Using Amazon Elastic MapReduce, you can instantly provision as much or as little 
capacity as you like to perform data-intensive tasks for applications such as 
web indexing, data mining, log file analysis, data warehousing, machine learning, 
financial analysis, scientific simulation, and bioinformatics research. 
Amazon Elastic MapReduce lets you focus on crunching or analyzing your data 
without having to worry about time-consuming set-up, management or tuning of 
Hadoop clusters or the compute capacity upon which they sit."

**MRJOB**
`Full Documentation` <http://packages.python.org/mrjob/>`_

To interface with Amazon EMR, the python module mrjob was developed to allow
python users to simply write their mapper and reducer functions, specify
initialization scripts and bootstrapping files, and let mrjob handle all
the work of interfacing with hadoop. It's an easy way to get your jobs
running on the cluster quickly.

"mrjob is a Python 2.5+ package that helps you write and run Hadoop Streaming jobs.

mrjob fully supports Amazon’s Elastic MapReduce (EMR) service, which allows 
you to buy time on a Hadoop cluster on an hourly basis. It also works with your own Hadoop cluster."

To install with pip, run in your linux command line:
`pip install mrjob` 

To understand the map-reduce algorithm and how you can use mrjob to implement it, a helpful
video to view is:
`PyCon 2011 MRJOB Presentation` <http://pyvideo.org/video/404/pycon-2011--mrjob--distributed-computing-for-ever>`

**How-To Run A Job**

0. Amazon Elastic MapReduce is available in limited areas worldwide. When you run your job, Amazon
will choose the cluster closest to you. But unfortunately if you don't live in the following general regions,
Amazon Elastic MapReduce won't work for you (yet!)

	* US East (Northern Virginia)
	* US West (Oregon)
	* US West (Northern California)
	* EU (Ireland)
	* Asia Pacific (Singapore)
	* Asia Pacific (Tokyo)
	* South America (Sao Paulo) Regions


1. Provide an input text file, full of formatted data or files to process. This
text file is then broken into small, processable units by the mrjob protocol.
Several different protocols may be chosen, depending on what format you've written
your input file in. `full details here <http://packages.python.org/mrjob/protocols.html?highlight=protocol#`_

2. Write your mrjobclass, and define the mapper and reducer functions. This can be quite simple, because
all you typically do in the class is call music21 functions, which do the computation, and return the result.
If you've written programs using music21, you can typically just copy and paste them in to the mapper function,
and, return the output. 

Be aware that both the mapper and reducer functions are run on all the instances on a subset of the input data from
the text file. Thus, design your mapper to run independently on every piece of input specified by the input protocol.

When writing your mrjob, it is advisable to wrap ALL your code in a `try`, `except` block, because
although mrjob tries hard to recover from failures, it would be a pity to run a big job and
generate lots of good data, then fail because one file had a parsing error.

The standard word-counting map-reduce algorithm, as given on the mrjob website, is below::

	from mrjob.job import MRJob

	class MRWordCounter(MRJob):
	    def mapper(self, key, line):
	        for word in line.split():
	            yield word, 1
	
	    def reducer(self, word, occurrences):
	        yield word, sum(occurrences)
	
	if __name__ == '__main__':
	    MRWordCounter.run()

A skeleton mrjob for music21 purposes might look like this:
	
	from music21 import *
	from mrjob.job import MRJob
	
	class myMusic21Process(MRJob):
	    def mapper(self, key, line):
	    	try:
		        # input might be a music file, and run music21 commands here to get data from the file
		        # yield all data as key, value pairs
		        yield 'someKey', someValue
			except:
				yield 'mappter_fail', line
	    def reducer(self, word, occurrences):
	    	try:
		        # this function could combine or process the output from the mapper
		        # if you don't want to use the reducer, don't include it
		        # output from the reducer is also in key, value pairs
		        yield word, sum(occurrences)
			except:
				yield 'reducer_fail', line
				
	if __name__ == '__main__':
	    MRWordCounter.run()


3. Test your mrjob by running it locally (on your computer)
`python nameOfMRJOB.py < NAME_OF_INPUT_FILE.txt > NAME_OF_DESIRED_OUTPUT_FILE`

4. Your output from the local run will be located in the same directory as your mrjob.py file, unless
you specified otherwise.

5. If everything works, then you're ready to run on EMR. First, get 
an `amazon web services account` <`http://aws.amazon.com/`>_ and sign up for EMR if you're not
already signed up. Take special note of your access key and secret access key, and be sure
to save your the .PEM file in a secure place. You won't be able to regenerate that, although you
can always generate new key pairs.

6. With your account all set up, you must provide a .mrjob.conf file before running your job, with
full specifications for running on EMR. See conf.rst for documentation on how to establish a conf file.

7. Now you're ready to deploy your job! Enter into command line
`python nameOfMRJOB.py -r emr < NAME_OF_INPUT_FILE.txt > NAME_OF_DESIRED_OUTPUT_FILE`

	Your terminal will show a brief, summary, log of what's happening with your job:

	* `Uploading input to ..., creating tmp directory...., writing master bootstrap script, Copying non-input files into`
		The first step that mrjob does is upload your scripts, bootstrapping files, data input, etc. to a folder in s3 (Amazon's
		online cloud storage system.) This won't take long.
	* `Creating Elastic MapReduce job flow`, `Job flow created with ID: .....` Now your job
	has been created! You will be able to view your job and its status real-time if you log into
	your aws account, click on AWS Management Console, then Amazon Elastic MapReduce tab. 
	You should see your job there with a status such as "STARTING". If at any time you'd like to t
	erminate your taks, you can easily do this through this window.
	* `Job launched 30.4s ago, status STARTING: Starting instances`: the remote CPUs are starting up...per your
	request...feel the power! =) Depending on availability, this may take a few seconds to a couple of minutes.
	* `Job launched 273.1s ago, status BOOTSTRAPPING: Running bootstrap actions`: now mrjob is configuring all those
	instances with the specific bootstrapping files you'd like them to have. In our case, this includes installing
	music21. You may also install Python 2.7 at this time (because Python 2.6 is default if running with ami version 2.1.0)
	The timeout (maximum time that mrjob will run bootstrapping before quitting) is 45 minutes. I surely hope your bootstrapping
doesn't take that long! Regardless, you're not charged for the time you spend bootstrapping =)
	* `Opening ssh tunnel to Hadoop job tracker`
	Yeah! This means your bootstrapping worked, and your jobs are about to be deployed. You now have the capability to ssh
	directly into your instances, if you'd like.
	* `Connect to job tracker at: http://localhost:#####/jobtracker.jsp` This is a very important line! This gives the url
	you can go to to view the status of your job. open this window now and you'll get much better status updates about the
	health of your job than in the terminal.
	* `Job launched 639.8s ago, status RUNNING: Running step (featureExtractionTest.bhadley.20120626.170931.990145: Step 1 of 1)
 map  50% reduce   0%` You will soon see lots of these lines...These let you know your job is in progress. The percentages
	are 'speculative' numbers, just a guess hadoop makes about the status of your job. Don't think that when they reach 100%
	your job will be done any time soon...This just indicates that 100% of the mappers have begun processing. For a better
	indication of the status of your job, use the url as notes above.
		* as your job runs, you can calculate how much it's costing and view how much has finished processing. When your job finishes,
		regardless of the end status (terminated, failed, successfully quit), any output from your mappers/reducers will be located
		in s3 in the appropriate bucket. This prevents you from losing valuable data if many of our mappers execute fine, 
		but just a few take forever and you terminate the job before they've completed.
	* if the job finished successfully, you'd see final data printed to the screen about counters, number of successful
	mappers/reducers/etc, and your final output will be streamed to the output file you specified. Your output will
	also be available on s3 permanently.

9. If something went wrong, and there was a fatal error, mrjob will shut down the instances and jobflow, 
and occasionally print a useful error message to the terminal. If not, it's always a good idea to
check the log files. Take note of the failed job flow's ID, and enter this into the command line:

`python -m mrjob.tools.emr.fetch_logs JOB_FLOW_IDE`

10. Now go to your amazon web services account online, and click the s3 tab. Navigate to logs within the
mrjob folder, and you should see your job flow id. Click through all the logs, full of terminal transcripts,
and hopefully you'll find your error and fix it for the next run. If the error happened during bootstrapping,
typically you won't be charged for that run. But if the error occurred during mapping or reducing, you're charged
for the full 1 hour of processing times the number of instances you chose. So it's wise to do you initial testing
with a small number of instances and m1.small instances.

11. While you're on your amazon account, click on the Elastic MapReduce tab and view the stats of your recent jobs.
You can also view your account details and history by navigating to account settings.

12. now...explore! The possibilities are endless....and much more complex than the examples provided here.