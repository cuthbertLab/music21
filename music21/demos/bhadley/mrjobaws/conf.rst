This is a sample configuration file that can be used to establish 
a mrjob on amazon web services using elastic map reduce.

For more information: http://packages.python.org/mrjob/configs-basics.html#mrjob-conf
Complete list of configuration options: http://packages.python.org/mrjob/configs-runners.html

The conf file must be in a specific format readable by mrjob. You can write
it in two formats: JSON, or YAML. Yaml looks cleaner and will cause you
less grief, so if you can install the yaml module for pyton: `sudo apt-get install python-yaml`

A standard mrjob conf file for running music21 tasks (using YAML) might look like this::
	runners: 
	  emr: 
	    aws_access_key_id: YOUR_ACCESS_KEY_HERE
	    aws_secret_access_key: YOUR_SECRET_ACCESS_KEY_HERE
	    ami_version: 2.1.0
	    num_ec2_instances: 10
	    ec2_instance_type: m1.small
	    ec2_key_pair: EMR
	    ec2_key_pair_file: /home/bhadley/Desktop/pem/EMRm21.pem
	    ssh_tunnel_to_job_tracker: true
	    enable_emr_debugging: true
	    bootstrap_scripts: ['/home/bhadley/Desktop/bootstrapScripts/install_music21.sh']
	    bootstrap_files: ['/home/bhadley/Desktop/bootstrapFiles/music21-2.0.0.tar.gz']
	    jobconf: 
	      mapred.task.timeout: 3600000
	      mapreduce.task.timeout: 3600000

And the same thing, but with JSON format::
	{"runners": 
	 {
	
	  "emr": 
	  {
	    "aws_access_key_id": "YOUR_ACCESS_KEY_HERE",
	    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY_HERE",
	    "ami_version": 2.1.0
	    "num_ec2_instances": 10,
	    "ec2_instance_type": "m1.small", 
	    "ec2_key_pair": EMR,
	    "ec2_key_pair_file": /directory/to/your/PEMFile/EMR.pem ,
	    "ssh_tunnel_to_job_tracker": true,
	    "enable_emr_debugging": true,
	    "bootstrap_scripts": ['/directory/to/music21/installation/script/install_music21.sh']
	    "bootstrap_files": ['/directory/to/tarred/music21/music21-2.0.0.tar.gz']
	  }
	 }
	
	}

*Notes on the above conf file*

* This file should be saved in as ~/.mrjob.conf That way mrjob will know where to look to find
the conf file.
* aws_access_key_id and aws_secret_access_key can be found from your amazon web services account
* num_ec2_instances: the number of slave instances you'd like to use
	The more you use, the faster the computation, but the more you pay. Note that
	you pay hourly, and this is not prorated so if your job only takes 20 minutes but runs
	on 20 instances, you pay for 20 full hours of computation. Run tests to
	establish efficient and cost-effective choices
* ami_version: Set this to the latest version, 2.1.0 (as of June 2012). Default is, unfortunately, the first
	version, 1.0. The latest version obviously has many more features, including Python 2.6 rather than 2.5 (on version 1.0)
	`Details on Versions Here` <http://docs.amazonwebservices.com/ElasticMapReduce/latest/DeveloperGuide/EnvironmentConfig_AMIVersion.html>

	* If you find you'll need a more recent version of Python than 2.6.6, you'll have to install Python
	during bootstrapping, and of course re-install mrjob as well. This will increase your bootstrapping
	time considerably! (500ish seconds!) To do so, append the file path to the tar.bz2 python installation
	folder in bootstrap_files, and include the scripin bootstrap_scripts.

* ec2_instance_type: the type of slave instances you'd like to use
	specs of all types of instances are available here: http://aws.amazon.com/ec2/instance-types/
	pricing is available here: http://aws.amazon.com/elasticmapreduce/pricing/
	*Standard Instances*
	==============					===============		====================================
	Instance Type					Price ($)			Normalized Instance Hours
	==============					===============		====================================
	m1.small 						0.095				1
	m1.large 						0.38				4
	m1.xlarge						0.76				8  
	*High Memory Instances*
	m2.xlarge						0.54				6	
	m2.2xlarge						1.11				12	
	m2.4xlarge						2.22				24
	*High-CPU Instances*
	c1.medium 						0.195				2
	c1.xlarge						0.78				8	
	*Cluster Compute Instances*
	cc1.4xlarge						1.57				16
	cc2.8xlarge						2.90				29
	*Cluster GPU Instances*
	cg1.4xlarge						2.52				25

	When you run your job, you will see the number of normalized instnace hours charged. Each normalized
	instance hour roughly costs $0.095. If you run 10 instances of the c1.medium for two hours, for example,
	you will see 40 (that's 10 instances * 2 normalized instance hours per instance * 2 hours time)
	you will be charged about $4 (that's 10 instances * 2 hours * $0.195 per hour = $3.9)
	FYI: this is roughly equivalent to 40*0.095=$3.80
* Bootstrapping
	Although I'm still investigating and I know there's got to be a better way,
	so far I've found that the amazon ec2 instances only have python 2.5 running
	on them. Thus, to install music21 you must install python 2.6 or 2.7, which
	takes about 10 minutes. Then you must install music21, another 5 minutes. And
	on top of that, I found that you also must re-install mrjob for python 2.7,
	bringing the total bootstrapping time up to a little under 20 minutes.
	But you aren't charged for this time, and for longer jobs the time is negligible,
	but I'm always searching for better ways to do this. Let me know if you've found one.
	
	For the time being, you'll have to provide the tarred folders of python2.7, music21, and mrjob
	for installation. If you've made changes to the music21 source-code, you'll want to prepare a new
	installation package (tar.gz it) and upload that. If you'd like to use the latest release of music21,
	simply download tar.gz folder from https://github.com/cuthbertLab/music21/releases
	
	The installation scripts in the conf file look like this::


		*install_python27.sh*
		
		#!/bin/bash
		tar jfx Python-2.7.2.tar.bz2
		cd Python-2.7.2
		./configure --with-threads --enable-shared
		make
		sudo make install
		sudo ln -s /usr/local/lib/libpython2.7.so.1.0 /usr/lib/
		sudo ln -s /usr/local/lib/libpython2.7.so /usr/

		*install_music21.sh*
		
		#!/bin/bash
		tar xvfz music21-2.0.5.tar.gz
		cd music21-2.0.5
		sudo python setup.py install
		
		*install_mrjob.sh*
		
		#!/bin/bash
		sudo apt-get install -y python-boto
		tar xvfz mrjob-0.3.3.2.tar.gz
		cd mrjob-0.3.3.2
		sudo python setup.py install
		
* EMR time-out. The default task timeout (the maximum time an instance is allowed to 
process a single step function) is by default 10 minutes. If the timeout is exceeded,
the job fails, terminates, and logs a timeout error. Booh. This is to help you keep track
of rougue instances. If you'd like to change this timeout, set `mapred.task.timeout`
and `mapreduce.task.timeout`. Units are in seconds. The reason to set both is to make
sure it works for whichever version of Hadoop the instance happens to be running.
		
		

		
		
		
		
		
		
		
		