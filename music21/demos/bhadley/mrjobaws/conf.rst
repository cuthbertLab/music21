This is a sample configuration file that can be used to establish 
a mrjob on amazon web services using elastic map reduce.

For more information: http://packages.python.org/mrjob/configs-basics.html#mrjob-conf
Complete list of configuration options: http://packages.python.org/mrjob/configs-runners.html

An example conf file for music21 mrjobs might look like this::

	{"runners": 
	 {
	
	  "emr": 
	  {
	    "aws_access_key_id": "YOUR_ACCESS_KEY_HERE",
	    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY_HERE",
	    "num_ec2_instances": 2, (The number of slave instances you'd like to use)
	    "ec2_instance_type": "m1.small", 
	    "ec2_key_pair": EMR,
	    "ec2_key_pair_file": /directory/to/your/PEMFile/EMR.pem ,
	    "ssh_tunnel_to_job_tracker": true, (should be true if you want to be able to debug)
	    "bootstrap_scripts": ['/directory/to/python/installation/script/install_python27.sh',
	    '/directory/to/music21/installation/script/install_music21.sh',
	    '/directory/to/mrjob/installation/script/install_mrjob.sh'],
	    "bootstrap_files": ['/directory/to/tarred/python2.7/Python-2.7.2.tar.bz2',
	    '/directory/to/tarred/music21/music21-1.0.tar.gz',
	    '/directory/to/tarred/mrjob/mrjob-0.3.3.2.tar.gz']
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
* ec2_instance_type: the type of slave instances you'd like to use
	specs of all types of instances are available here: http://aws.amazon.com/ec2/instance-types/
	pricing is available here: http://aws.amazon.com/elasticmapreduce/pricing/
	*Standard Instances*
	* m1.small
	* m1.medium
	* m1.large
	* m1.xlarge
	* Micro Instances*
	* t1.micro
	*High Memory Instances*
	* m2.xlarge
	* m2.2xlarge
	* m2.4xlarge
	*High-CPU Instances*
	* c1.medium
	* c1.xlarge
	*Cluster Compute Instances*
	* cc1.4xlarge
	* cc2.8xlarge
	*Cluster GPU Instances*
	* cg1.4xlarge

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
	simply download tar.gz folder from  http://code.google.com/p/music21/downloads/list
	
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
		tar xvfz music21-0.6.3.b3.tar.gz
		cd music21-0.6.3.b3
		sudo python setup.py install
		
		*install_mrjob.sh*
		
		#!/bin/bash
		sudo apt-get install -y python-boto
		tar xvfz mrjob-0.3.3.2.tar.gz
		cd mrjob-0.3.3.2
		sudo python setup.py install