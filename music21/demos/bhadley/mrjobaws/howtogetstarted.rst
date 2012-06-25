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
Dean, J., Ghemawat,S.(2004).“MapReduce:Simplified data processing on large clusters,” Proceedings of the 6th Symposium on Operating System Design and Implementation, pp. 137–50.

From their paper:
"MapReduce is a programming model and an associated implementation for processing
and generating large datasets that is amenable to a broad variety of real-world tasks.
Users specify the computation in terms of a map and a reduce function, and the under-
lying runtime system automatically parallelizes the computation across large-scale clusters of
machines, handles machine failures, and schedules inter-machine communication to make efficient use of the network and disks. Programmers find the system easy to use: more than ten
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
	
	fro music21 import *
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
you specified otherwise

5. If everything works, then you're ready to run on EMR. First, get 
an `amazon web services account` <`http://aws.amazon.com/`>_ and sign up for EMR if you're not
already signed up. Take special note of your access key and secret access key, and be sure
to save your the .PEM file in a secure place. You won't be able to regenerate that, although you
can always generate new key pairs.

6. With your account all set up, you must provide a .mrjob.conf file before running your job, with
full specifications for running on EMR. See conf.rst for documentation on how to establish a conf file.

7. Now you're ready to deploy your job! Enter into command line
`python nameOfMRJOB.py -r emr < NAME_OF_INPUT_FILE.txt > NAME_OF_DESIRED_OUTPUT_FILE`

Hopefully you will see a transcript of the process in the command shell. At some point
bootstrapping will begin, and because you're installing the entirety of python2.7, music21, and mrjob,
this unfortunately will take about 15 minutes. If anyone makes any breakthroughs about how to 
get this faster, please let me know!

8. After bootstrapping, you will see readouts of the percentage of mapping done and the percentage of 
reducing done. If the job was successful, the final count will be 100%, and the job will terminate. Your
output file (located in whatever directory you specified) will contain the run's output.

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

12. now...explore! The possibilities are endless....